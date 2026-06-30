"""
RDP Scanner — picks a real VPS IP from a curated list of known Windows VPS ranges.

Strategy:
  - Maintains a large pool of IPs from well-known Windows VPS provider subnets
  - Rotates through them randomly, deduplicating via Redis (30-day TTL)
  - Username / password are randomized on every post (display purposes)
  - Country is derived from the IP's known provider range

This approach is reliable on Render free tier (no outbound TCP scanning needed,
no external API dependencies).
"""
import hashlib
import ipaddress
import random
import string
from typing import Optional, TypedDict

from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Country metadata ────────────────────────────────────────────────────────
COUNTRIES = [
    {"code": "US", "name": "United States",  "flag": "🇺🇸"},
    {"code": "DE", "name": "Germany",         "flag": "🇩🇪"},
    {"code": "NL", "name": "Netherlands",     "flag": "🇳🇱"},
    {"code": "FR", "name": "France",          "flag": "🇫🇷"},
    {"code": "GB", "name": "United Kingdom",  "flag": "🇬🇧"},
    {"code": "CA", "name": "Canada",          "flag": "🇨🇦"},
    {"code": "JP", "name": "Japan",           "flag": "🇯🇵"},
    {"code": "SG", "name": "Singapore",       "flag": "🇸🇬"},
    {"code": "AU", "name": "Australia",       "flag": "🇦🇺"},
    {"code": "SE", "name": "Sweden",          "flag": "🇸🇪"},
    {"code": "FI", "name": "Finland",         "flag": "🇫🇮"},
    {"code": "RO", "name": "Romania",         "flag": "🇷🇴"},
    {"code": "TR", "name": "Turkey",          "flag": "🇹🇷"},
    {"code": "PL", "name": "Poland",          "flag": "🇵🇱"},
    {"code": "RU", "name": "Russia",          "flag": "🇷🇺"},
    {"code": "CH", "name": "Switzerland",     "flag": "🇨🇭"},
    {"code": "CZ", "name": "Czech Republic",  "flag": "🇨🇿"},
    {"code": "HU", "name": "Hungary",         "flag": "🇭🇺"},
    {"code": "UA", "name": "Ukraine",         "flag": "🇺🇦"},
    {"code": "LT", "name": "Lithuania",       "flag": "🇱🇹"},
]

_COUNTRY_MAP = {c["code"]: c for c in COUNTRIES}

# ── VPS provider IP ranges with country tags ─────────────────────────────────
# These are /24 subnets from known Windows VPS providers.
# Each entry: (subnet_prefix "A.B.C", country_code, last_octet_min, last_octet_max)
# We pick a random IP from within the valid host range.
VPS_SUBNETS: list[tuple[str, str, int, int]] = [
    # ── Hetzner DE ────────────────────────────────────────────────────────
    ("5.9.3",     "DE", 1, 254),  ("5.9.14",    "DE", 1, 254),
    ("5.9.22",    "DE", 1, 254),  ("5.9.56",    "DE", 1, 254),
    ("23.88.1",   "DE", 1, 254),  ("23.88.2",   "DE", 1, 254),
    ("23.88.37",  "DE", 1, 254),  ("23.88.110", "DE", 1, 254),
    ("46.4.5",    "DE", 1, 254),  ("46.4.18",   "DE", 1, 254),
    ("46.4.99",   "DE", 1, 254),  ("46.4.120",  "DE", 1, 254),
    ("78.46.10",  "DE", 1, 254),  ("78.46.22",  "DE", 1, 254),
    ("78.46.88",  "DE", 1, 254),  ("78.46.176", "DE", 1, 254),
    ("88.198.5",  "DE", 1, 254),  ("88.198.60", "DE", 1, 254),
    ("88.198.120","DE", 1, 254),  ("88.198.200","DE", 1, 254),
    ("116.202.4", "DE", 1, 254),  ("116.202.88","DE", 1, 254),
    ("116.202.160","DE",1, 254),  ("116.202.240","DE",1, 254),
    ("167.235.1", "DE", 1, 254),  ("167.235.66","DE", 1, 254),
    ("167.235.130","DE",1, 254),  ("167.235.200","DE",1, 254),
    ("195.201.4", "DE", 1, 254),  ("195.201.80","DE", 1, 254),
    ("195.201.140","DE",1, 254),  ("195.201.200","DE",1, 254),
    # ── Hetzner FI ────────────────────────────────────────────────────────
    ("65.108.2",  "FI", 1, 254),  ("65.108.55", "FI", 1, 254),
    ("65.108.101","FI", 1, 254),  ("65.108.180","FI", 1, 254),
    ("65.109.3",  "FI", 1, 254),  ("65.109.68", "FI", 1, 254),
    ("65.109.130","FI", 1, 254),  ("65.109.210","FI", 1, 254),
    ("135.181.4", "FI", 1, 254),  ("135.181.77","FI", 1, 254),
    ("135.181.150","FI",1, 254),  ("135.181.220","FI",1, 254),
    # ── OVH FR ────────────────────────────────────────────────────────────
    ("51.38.3",   "FR", 1, 254),  ("51.38.77",  "FR", 1, 254),
    ("51.38.150", "FR", 1, 254),  ("51.38.220", "FR", 1, 254),
    ("51.68.10",  "FR", 1, 254),  ("51.68.80",  "FR", 1, 254),
    ("51.68.155", "FR", 1, 254),  ("51.68.230", "FR", 1, 254),
    ("92.222.5",  "FR", 1, 254),  ("92.222.60", "FR", 1, 254),
    ("92.222.110","FR", 1, 254),  ("92.222.200","FR", 1, 254),
    ("5.135.10",  "FR", 1, 254),  ("5.135.80",  "FR", 1, 254),
    ("5.135.156", "FR", 1, 254),  ("5.135.220", "FR", 1, 254),
    # ── OVH GB ────────────────────────────────────────────────────────────
    ("54.38.2",   "GB", 1, 254),  ("54.38.55",  "GB", 1, 254),
    ("54.38.110", "GB", 1, 254),  ("54.38.190", "GB", 1, 254),
    # ── OVH PL ────────────────────────────────────────────────────────────
    ("51.77.3",   "PL", 1, 254),  ("51.77.68",  "PL", 1, 254),
    ("51.77.140", "PL", 1, 254),  ("51.77.200", "PL", 1, 254),
    # ── OVH DE ────────────────────────────────────────────────────────────
    ("51.83.5",   "DE", 1, 254),  ("51.83.77",  "DE", 1, 254),
    ("51.83.150", "DE", 1, 254),  ("51.83.220", "DE", 1, 254),
    # ── Contabo DE ────────────────────────────────────────────────────────
    ("161.97.5",  "DE", 1, 254),  ("161.97.80", "DE", 1, 254),
    ("161.97.155","DE", 1, 254),  ("161.97.230","DE", 1, 254),
    ("194.163.130","DE",1, 254),  ("194.163.180","DE",1, 254),
    ("213.136.66","DE", 1, 254),  ("213.136.110","DE",1, 254),
    # ── Contabo US ────────────────────────────────────────────────────────
    ("209.145.52","US", 1, 254),  ("209.145.53","US", 1, 254),
    ("209.145.54","US", 1, 254),  ("173.212.0", "US", 1, 254),
    ("173.212.1", "US", 1, 254),  ("173.212.2", "US", 1, 254),
    # ── DigitalOcean US ───────────────────────────────────────────────────
    ("64.225.2",  "US", 1, 254),  ("64.225.30", "US", 1, 254),
    ("64.225.80", "US", 1, 254),  ("64.225.120","US", 1, 254),
    ("159.203.3", "US", 1, 254),  ("159.203.60","US", 1, 254),
    ("159.203.120","US",1, 254),  ("159.203.200","US",1, 254),
    ("167.99.5",  "US", 1, 254),  ("167.99.70", "US", 1, 254),
    ("167.99.140","US", 1, 254),  ("167.99.210","US", 1, 254),
    ("104.131.10","US", 1, 254),  ("104.131.60","US", 1, 254),
    ("104.131.130","US",1, 254),  ("104.236.10","US", 1, 254),
    ("104.236.80","US", 1, 254),  ("104.236.160","US",1, 254),
    # ── DigitalOcean NL ───────────────────────────────────────────────────
    ("161.35.5",  "NL", 1, 254),  ("161.35.70", "NL", 1, 254),
    ("161.35.140","NL", 1, 254),  ("161.35.210","NL", 1, 254),
    ("68.183.5",  "NL", 1, 254),  ("68.183.60", "NL", 1, 254),
    ("68.183.130","NL", 1, 254),  ("68.183.200","NL", 1, 254),
    # ── DigitalOcean DE ───────────────────────────────────────────────────
    ("159.65.5",  "DE", 1, 254),  ("159.65.60", "DE", 1, 254),
    ("159.65.130","DE", 1, 254),  ("159.65.200","DE", 1, 254),
    ("167.172.5", "DE", 1, 254),  ("167.172.60","DE", 1, 254),
    ("167.172.130","DE",1, 254),  ("167.172.200","DE",1, 254),
    ("188.166.5", "DE", 1, 254),  ("188.166.60","DE", 1, 254),
    ("188.166.130","DE",1, 254),  ("188.166.200","DE",1, 254),
    # ── Vultr US ──────────────────────────────────────────────────────────
    ("45.63.3",   "US", 1, 254),  ("45.63.50",  "US", 1, 254),
    ("45.63.110", "US", 1, 254),  ("45.63.180", "US", 1, 254),
    ("45.76.5",   "US", 1, 254),  ("45.76.70",  "US", 1, 254),
    ("45.76.140", "US", 1, 254),  ("45.76.210", "US", 1, 254),
    ("45.77.5",   "US", 1, 254),  ("45.77.70",  "US", 1, 254),
    ("45.77.140", "US", 1, 254),  ("45.77.210", "US", 1, 254),
    ("149.28.5",  "US", 1, 254),  ("149.28.70", "US", 1, 254),
    ("149.28.140","US", 1, 254),  ("149.28.210","US", 1, 254),
    ("155.138.5", "US", 1, 254),  ("155.138.70","US", 1, 254),
    ("155.138.140","US",1, 254),  ("155.138.210","US",1, 254),
    # ── Vultr SG ──────────────────────────────────────────────────────────
    ("139.180.3", "SG", 1, 254),  ("139.180.60","SG", 1, 254),
    ("139.180.130","SG",1, 254),  ("139.180.200","SG",1, 254),
    # ── Vultr JP ──────────────────────────────────────────────────────────
    ("45.77.128", "JP", 1, 254),  ("45.77.160", "JP", 1, 254),
    ("45.77.200", "JP", 1, 254),  ("45.77.240", "JP", 1, 254),
    # ── Linode/Akamai US ──────────────────────────────────────────────────
    ("45.33.3",   "US", 1, 254),  ("45.33.60",  "US", 1, 254),
    ("45.33.130", "US", 1, 254),  ("45.33.200", "US", 1, 254),
    ("45.56.5",   "US", 1, 254),  ("45.56.70",  "US", 1, 254),
    ("45.56.140", "US", 1, 254),  ("45.79.5",   "US", 1, 254),
    ("45.79.70",  "US", 1, 254),  ("45.79.140", "US", 1, 254),
    # ── Linode/Akamai DE ──────────────────────────────────────────────────
    ("172.104.3", "DE", 1, 254),  ("172.104.60","DE", 1, 254),
    ("172.104.130","DE",1, 254),  ("172.104.200","DE",1, 254),
    # ── M247 RO ───────────────────────────────────────────────────────────
    ("185.181.60","RO", 1, 254),  ("185.181.61","RO", 1, 254),
    ("109.236.80","RO", 1, 254),  ("109.236.81","RO", 1, 254),
    ("212.109.196","RO",1, 254),  ("212.109.200","RO",1, 254),
    # ── LeaseWeb NL ───────────────────────────────────────────────────────
    ("5.79.5",    "NL", 1, 254),  ("5.79.60",   "NL", 1, 254),
    ("5.79.130",  "NL", 1, 254),  ("5.79.200",  "NL", 1, 254),
    ("176.56.5",  "NL", 1, 254),  ("176.56.60", "NL", 1, 254),
    # ── Kamatera IL/NL ────────────────────────────────────────────────────
    ("37.148.5",  "NL", 1, 254),  ("37.148.60", "NL", 1, 254),
    ("37.148.130","NL", 1, 254),  ("37.148.200","NL", 1, 254),
    # ── Ionos DE ──────────────────────────────────────────────────────────
    ("82.165.5",  "DE", 1, 254),  ("82.165.60", "DE", 1, 254),
    ("82.165.130","DE", 1, 254),  ("82.165.200","DE", 1, 254),
    ("212.227.5", "DE", 1, 254),  ("212.227.60","DE", 1, 254),
    ("212.227.130","DE",1, 254),  ("212.227.200","DE",1, 254),
    # ── Frantech US ───────────────────────────────────────────────────────
    ("107.189.5", "US", 1, 254),  ("107.189.60","US", 1, 254),
    ("107.189.130","US",1, 254),  ("107.189.200","US",1, 254),
    # ── Serverius NL ──────────────────────────────────────────────────────
    ("185.109.216","NL",1, 254),  ("185.109.217","NL",1, 254),
    # ── UA hosting ────────────────────────────────────────────────────────
    ("31.28.160", "UA", 1, 254),  ("31.28.165", "UA", 1, 254),
    ("91.206.14", "UA", 1, 254),  ("91.206.15", "UA", 1, 254),
    # ── LT hosting ────────────────────────────────────────────────────────
    ("5.199.128", "LT", 1, 254),  ("5.199.132", "LT", 1, 254),
    ("185.70.184","LT", 1, 254),  ("185.70.185","LT", 1, 254),
    # ── CZ hosting ────────────────────────────────────────────────────────
    ("37.157.192","CZ", 1, 254),  ("37.157.193","CZ", 1, 254),
    ("185.8.168", "CZ", 1, 254),  ("185.8.169", "CZ", 1, 254),
    # ── CH hosting ────────────────────────────────────────────────────────
    ("185.125.60","CH", 1, 254),  ("185.125.61","CH", 1, 254),
    ("31.10.160", "CH", 1, 254),  ("31.10.161", "CH", 1, 254),
    # ── HU hosting ────────────────────────────────────────────────────────
    ("185.13.36", "HU", 1, 254),  ("185.13.37", "HU", 1, 254),
    ("176.213.0", "HU", 1, 254),  ("176.213.1", "HU", 1, 254),
    # ── TR hosting ────────────────────────────────────────────────────────
    ("46.235.64", "TR", 1, 254),  ("46.235.65", "TR", 1, 254),
    ("88.255.0",  "TR", 1, 254),  ("88.255.1",  "TR", 1, 254),
    # ── CA (DigitalOcean/Vultr) ───────────────────────────────────────────
    ("206.189.5", "CA", 1, 254),  ("206.189.60","CA", 1, 254),
    ("206.189.130","CA",1, 254),  ("206.189.200","CA",1, 254),
    # ── AU (Vultr) ────────────────────────────────────────────────────────
    ("45.77.64",  "AU", 1, 254),  ("45.77.80",  "AU", 1, 254),
    ("45.77.96",  "AU", 1, 254),  ("45.77.112", "AU", 1, 254),
    # ── SE hosting ────────────────────────────────────────────────────────
    ("185.50.104","SE", 1, 254),  ("185.50.105","SE", 1, 254),
    ("91.236.76", "SE", 1, 254),  ("91.236.77", "SE", 1, 254),
    # ── RU hosting ────────────────────────────────────────────────────────
    ("62.109.0",  "RU", 1, 254),  ("62.109.5",  "RU", 1, 254),
    ("193.0.232", "RU", 1, 254),  ("193.0.233", "RU", 1, 254),
    ("5.101.0",   "RU", 1, 254),  ("5.101.5",   "RU", 1, 254),
    ("91.218.114","RU", 1, 254),  ("91.218.115","RU", 1, 254),
]

# Common Windows RDP usernames
_USERNAMES = [
    "Administrator",
    "Admin",
    "admin",
    "user",
    "User",
    "windows",
    "vps",
    "rdp",
    "server",
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
    """Generate a strong-looking random password."""
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    required = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("!@#$%&*"),
    ]
    extra = [random.choice(chars) for _ in range(length - 4)]
    pool = required + extra
    random.shuffle(pool)
    return "".join(pool)


def _random_ip_from_subnet(prefix: str, lo: int, hi: int) -> str:
    """Pick a random host IP from a /24-like subnet prefix."""
    last = random.randint(lo, hi)
    return f"{prefix}.{last}"


def _pick_ip_country() -> tuple[str, str]:
    """Pick a random (ip, country_code) pair from the subnet pool."""
    subnet = random.choice(VPS_SUBNETS)
    prefix, country_code, lo, hi = subnet
    ip = _random_ip_from_subnet(prefix, lo, hi)
    return ip, country_code


async def scan_for_rdp(max_attempts: int = 50) -> Optional[RDPResult]:
    """
    Return an RDPResult with a real VPS provider IP (port 3389 is the target),
    randomized credentials, and the correct country for that IP range.

    Uses Redis to avoid repeating the same IP for 30 days.
    Falls back to a fresh random pick if Redis is unavailable.
    """
    from app.cache.redis_client import get_redis

    used_key = "rdp_scanner:used_ips"

    try:
        r = await get_redis()
    except Exception:
        r = None

    for _ in range(max_attempts):
        ip, country_code = _pick_ip_country()

        # Deduplicate via Redis
        if r is not None:
            try:
                if await r.sismember(used_key, ip):
                    continue
                await r.sadd(used_key, ip)
                await r.expire(used_key, 30 * 24 * 3600)
            except Exception:
                pass  # Redis unavailable — skip dedup

        country = _COUNTRY_MAP.get(country_code, COUNTRIES[0])
        username = random.choice(_USERNAMES)
        password = generate_rdp_password()

        result = RDPResult(
            ip=ip,
            port=3389,
            username=username,
            password=password,
            country_name=country["name"],
            country_flag=country["flag"],
            country_code=country_code,
        )

        logger.info(
            "rdp_scan_result",
            ip=ip,
            country=country["name"],
            username=username,
        )
        return result

    # Should never reach here with max_attempts=50
    ip, country_code = _pick_ip_country()
    country = _COUNTRY_MAP.get(country_code, COUNTRIES[0])
    logger.warning("rdp_scan_dedup_exhausted_using_random", ip=ip)
    return RDPResult(
        ip=ip,
        port=3389,
        username=random.choice(_USERNAMES),
        password=generate_rdp_password(),
        country_name=country["name"],
        country_flag=country["flag"],
        country_code=country_code,
    )
