"""
RDP Scanner — scans countries in rotation for open port 3389.
Country rotation and IP deduplication are tracked in Redis.
Each scan uses a different country; no IP is ever repeated.
"""
import asyncio
import random
import string
from typing import Optional, TypedDict

from app.services.scanner.ip_ranges import get_country_cidr_blocks
from app.services.scanner.port_scanner import scan_port
from app.cache.redis_client import get_redis
from app.core.logging import get_logger

logger = get_logger(__name__)

REDIS_KEY_COUNTRY_INDEX = "rdp_scanner:country_index"
REDIS_KEY_USED_IPS = "rdp_scanner:used_ips"
USED_IP_TTL = 30 * 24 * 3600  # 30 days

COUNTRIES = [
    {"code": "US", "name": "United States", "flag": "\U0001f1fa\U0001f1f8"},
    {"code": "DE", "name": "Germany",        "flag": "\U0001f1e9\U0001f1ea"},
    {"code": "NL", "name": "Netherlands",    "flag": "\U0001f1f3\U0001f1f1"},
    {"code": "FR", "name": "France",         "flag": "\U0001f1eb\U0001f1f7"},
    {"code": "GB", "name": "United Kingdom", "flag": "\U0001f1ec\U0001f1e7"},
    {"code": "CA", "name": "Canada",         "flag": "\U0001f1e8\U0001f1e6"},
    {"code": "JP", "name": "Japan",          "flag": "\U0001f1ef\U0001f1f5"},
    {"code": "SG", "name": "Singapore",      "flag": "\U0001f1f8\U0001f1ec"},
    {"code": "AU", "name": "Australia",      "flag": "\U0001f1e6\U0001f1fa"},
    {"code": "SE", "name": "Sweden",         "flag": "\U0001f1f8\U0001f1ea"},
    {"code": "FI", "name": "Finland",        "flag": "\U0001f1eb\U0001f1ee"},
    {"code": "NO", "name": "Norway",         "flag": "\U0001f1f3\U0001f1f4"},
    {"code": "CH", "name": "Switzerland",    "flag": "\U0001f1e8\U0001f1ed"},
    {"code": "PL", "name": "Poland",         "flag": "\U0001f1f5\U0001f1f1"},
    {"code": "RO", "name": "Romania",        "flag": "\U0001f1f7\U0001f1f4"},
    {"code": "BR", "name": "Brazil",         "flag": "\U0001f1e7\U0001f1f7"},
    {"code": "KR", "name": "South Korea",    "flag": "\U0001f1f0\U0001f1f7"},
    {"code": "RU", "name": "Russia",         "flag": "\U0001f1f7\U0001f1fa"},
    {"code": "TR", "name": "Turkey",         "flag": "\U0001f1f9\U0001f1f7"},
    {"code": "IN", "name": "India",          "flag": "\U0001f1ee\U0001f1f3"},
    {"code": "IT", "name": "Italy",          "flag": "\U0001f1ee\U0001f1f9"},
    {"code": "ES", "name": "Spain",          "flag": "\U0001f1ea\U0001f1f8"},
    {"code": "UA", "name": "Ukraine",        "flag": "\U0001f1fa\U0001f1e6"},
    {"code": "CZ", "name": "Czech Republic", "flag": "\U0001f1e8\U0001f1ff"},
    {"code": "HU", "name": "Hungary",        "flag": "\U0001f1ed\U0001f1fa"},
]


class RDPResult(TypedDict):
    ip: str
    port: int
    username: str
    password: str
    country_name: str
    country_flag: str
    country_code: str


def generate_rdp_password(length: int = 14) -> str:
    """Generate a strong random password — uppercase, lowercase, digits, symbols."""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    required = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*"),
    ]
    extra = [random.choice(chars) for _ in range(length - 4)]
    pool = required + extra
    random.shuffle(pool)
    return "".join(pool)


async def get_next_country() -> dict:
    """Return next country in rotation and advance the index (wraps around)."""
    r = await get_redis()
    idx = await r.incr(REDIS_KEY_COUNTRY_INDEX)   # atomic; starts at 1
    country = COUNTRIES[(idx - 1) % len(COUNTRIES)]
    logger.info("rdp_scanner_country_selected",
                country=country["name"], rotation_index=idx)
    return country


async def _is_ip_used(ip: str) -> bool:
    r = await get_redis()
    return bool(await r.sismember(REDIS_KEY_USED_IPS, ip))


async def _mark_ip_used(ip: str) -> None:
    r = await get_redis()
    await r.sadd(REDIS_KEY_USED_IPS, ip)
    await r.expire(REDIS_KEY_USED_IPS, USED_IP_TTL)


async def scan_for_rdp(max_ips: int = 5000) -> Optional[RDPResult]:
    """
    Scan countries in rotation until a unique unused RDP IP is found.
    Retries the next country automatically — never gives up until all 25
    countries have been tried in one round.
    """
    for attempt in range(len(COUNTRIES)):
        country = await get_next_country()
        country_code = country["code"]
        country_name = country["name"]
        country_flag = country["flag"]

        try:
            logger.info("rdp_scan_starting",
                        country=country_name, code=country_code, attempt=attempt + 1)
            cidrs = await get_country_cidr_blocks(country_code)
            found_ips = await scan_port(cidrs, port=3389, max_ips=max_ips, timeout=1.2)
            logger.info("rdp_scan_finished",
                        country=country_name, open_ports_found=len(found_ips))

            if not found_ips:
                logger.warning("rdp_scan_no_open_ports_trying_next",
                               country=country_name, attempt=attempt + 1)
                continue

            random.shuffle(found_ips)
            for ip in found_ips:
                if not await _is_ip_used(ip):
                    await _mark_ip_used(ip)
                    password = generate_rdp_password()
                    logger.info("rdp_scan_ip_selected",
                                country=country_name, ip=ip, attempt=attempt + 1)
                    return RDPResult(
                        ip=ip,
                        port=3389,
                        username="Administrator",
                        password=password,
                        country_name=country_name,
                        country_flag=country_flag,
                        country_code=country_code,
                    )

            logger.warning("rdp_scan_all_ips_used_trying_next",
                           country=country_name, total=len(found_ips), attempt=attempt + 1)

        except Exception as e:
            logger.error("rdp_scan_error_trying_next",
                         country=country_name, error=str(e), attempt=attempt + 1)

    logger.error("rdp_scan_exhausted_all_countries_no_ip_found")
    return None
