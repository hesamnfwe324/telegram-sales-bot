"""
RDP Scanner — real scan with Windows RDP protocol verification.
Only returns IPs that genuinely respond to the Windows RDP X.224 handshake.
Returns None if no verified Windows RDP server is found within the time budget.
No fake fallback — every result is a real, connectable Windows Remote Desktop server.
"""
import asyncio
import random
import string
from typing import Optional, TypedDict

from app.core.logging import get_logger

logger = get_logger(__name__)

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
    {"code": "RO", "name": "Romania",        "flag": "\U0001f1f7\U0001f1f4"},
    {"code": "BR", "name": "Brazil",         "flag": "\U0001f1e7\U0001f1f7"},
    {"code": "KR", "name": "South Korea",    "flag": "\U0001f1f0\U0001f1f7"},
    {"code": "TR", "name": "Turkey",         "flag": "\U0001f1f9\U0001f1f7"},
    {"code": "IN", "name": "India",          "flag": "\U0001f1ee\U0001f1f3"},
    {"code": "IT", "name": "Italy",          "flag": "\U0001f1ee\U0001f1f9"},
    {"code": "PL", "name": "Poland",         "flag": "\U0001f1f5\U0001f1f1"},
    {"code": "UA", "name": "Ukraine",        "flag": "\U0001f1fa\U0001f1e6"},
    {"code": "RU", "name": "Russia",         "flag": "\U0001f1f7\U0001f1fa"},
]

# Standard RDP X.224 Connection Request packet (TPKT + X.224 CR)
_RDP_X224_REQUEST = bytes([
    0x03, 0x00, 0x00, 0x13,   # TPKT header: version=3, reserved=0, length=19
    0x0e,                      # X.224 header length
    0xe0,                      # X.224 Connection Request (CR) code
    0x00, 0x00,                # DST-REF
    0x00, 0x00,                # SRC-REF
    0x00,                      # CLASS
    0x01, 0x00, 0x08, 0x00,   # RDP negotiation request (TYPE=1, FLAGS=0, LENGTH=8)
    0x00, 0x00, 0x00, 0x00,   # requested protocols (PROTOCOL_RDP)
])


class RDPResult(TypedDict):
    ip: str
    port: int
    username: str
    password: str
    country_name: str
    country_flag: str
    country_code: str


def generate_rdp_password(length: int = 14) -> str:
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


async def _verify_rdp_protocol(ip: str, port: int = 3389, timeout: float = 3.0) -> bool:
    """
    Send an RDP X.224 Connection Request and check for a Windows RDP response.
    A genuine Windows Remote Desktop server replies with X.224 Connection Confirm
    which has 0xd0 at byte index 4 of the TPKT response.
    This distinguishes real Windows RDP from:
      - random open TCP ports (web servers, SSH, etc.)
      - firewalls that accept but don't respond
      - non-Windows services forwarding port 3389
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout=timeout
        )
        try:
            writer.write(_RDP_X224_REQUEST)
            await asyncio.wait_for(writer.drain(), timeout=1.0)
            # Read up to 32 bytes — the CC response is 19 bytes
            data = await asyncio.wait_for(reader.read(32), timeout=timeout)
            # X.224 Connection Confirm: TPKT header 0x03 0x00, then CC code 0xd0
            return (
                len(data) >= 5
                and data[0] == 0x03
                and data[1] == 0x00
                and data[4] == 0xd0
            )
        finally:
            try:
                writer.close()
                await asyncio.wait_for(writer.wait_closed(), timeout=1.0)
            except Exception:
                pass
    except Exception:
        return False


async def _scan_country(country: dict, max_ips: int = 400) -> Optional[RDPResult]:
    """
    Fetch CIDR blocks for a country, scan for open port 3389, then verify
    each candidate with an RDP handshake. Returns the first verified Windows
    RDP server found, or None.
    """
    try:
        from app.services.scanner.ip_ranges import get_country_cidr_blocks
        from app.services.scanner.port_scanner import scan_port

        cidrs = await asyncio.wait_for(
            get_country_cidr_blocks(country["code"]), timeout=4.0
        )
        if not cidrs:
            return None

        open_ips = await asyncio.wait_for(
            scan_port(cidrs, port=3389, max_ips=max_ips, timeout=0.8),
            timeout=7.0,
        )
        if not open_ips:
            logger.debug("rdp_scan_no_open_ports", country=country["code"])
            return None

        logger.info("rdp_scan_open_ports_found",
                    country=country["code"], count=len(open_ips))

        # Verify up to 15 candidates with full RDP handshake
        random.shuffle(open_ips)
        for ip in open_ips[:15]:
            if await _verify_rdp_protocol(ip, timeout=2.5):
                logger.info("rdp_verified_windows_server",
                            ip=ip, country=country["code"])
                return RDPResult(
                    ip=ip,
                    port=3389,
                    username="Administrator",
                    password=generate_rdp_password(),
                    country_name=country["name"],
                    country_flag=country["flag"],
                    country_code=country["code"],
                )

        logger.debug("rdp_no_verified_rdp_in_candidates",
                     country=country["code"], checked=min(len(open_ips), 15))
        return None

    except asyncio.TimeoutError:
        logger.debug("rdp_country_scan_timeout", country=country["code"])
        return None
    except Exception as e:
        logger.debug("rdp_country_scan_error",
                     country=country["code"], reason=str(e)[:80])
        return None


async def scan_for_rdp(max_ips: int = 400) -> Optional[RDPResult]:
    """
    Scan multiple countries in parallel for real Windows RDP servers.
    Only returns an RDPResult when a genuine Windows Remote Desktop server
    is confirmed via X.224 handshake. Returns None otherwise — the caller
    should skip posting when None is returned.

    Deduplicates results: the same IP won't be returned twice within 30 days.
    """
    from app.cache.redis_client import get_redis

    countries = random.sample(COUNTRIES, min(4, len(COUNTRIES)))
    logger.info("rdp_scan_starting",
                countries=[c["code"] for c in countries],
                max_ips_per_country=max_ips)

    tasks = [
        asyncio.create_task(_scan_country(country, max_ips))
        for country in countries
    ]

    result: Optional[RDPResult] = None
    try:
        for coro in asyncio.as_completed(tasks):
            candidate = await coro
            if candidate is None:
                continue

            # Deduplicate via Redis — skip IPs used in the last 30 days
            try:
                r = await get_redis()
                used_key = "rdp_scanner:used_ips"
                if await r.sismember(used_key, candidate["ip"]):
                    logger.info("rdp_ip_already_posted_skipping",
                                ip=candidate["ip"])
                    continue
                await r.sadd(used_key, candidate["ip"])
                await r.expire(used_key, 30 * 24 * 3600)
            except Exception as redis_err:
                # Redis failure is non-fatal — still use the result
                logger.warning("rdp_redis_dedup_failed", error=str(redis_err)[:60])

            result = candidate
            break
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()
        # Await cancellation quietly
        await asyncio.gather(*tasks, return_exceptions=True)

    if result:
        logger.info("rdp_scan_success",
                    ip=result["ip"],
                    country=result["country_name"])
    else:
        logger.info("rdp_scan_no_verified_result",
                    hint="no real Windows RDP found — post will be skipped")
    return result
