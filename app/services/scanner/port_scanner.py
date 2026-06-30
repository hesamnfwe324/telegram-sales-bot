import asyncio
import ipaddress
import random
from typing import List, Optional

# Number of concurrent TCP connection attempts
SEMAPHORE_LIMIT = 400


async def _check_port(
    ip: str,
    port: int,
    timeout: float,
    semaphore: asyncio.Semaphore,
) -> Optional[str]:
    """Attempt TCP connection to ip:port. Returns the IP on success, None on failure."""
    async with semaphore:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=timeout
            )
            try:
                writer.close()
                await asyncio.wait_for(writer.wait_closed(), timeout=0.5)
            except Exception:
                pass
            return ip
        except Exception:
            return None


async def scan_port(
    cidrs: List[str],
    port: int = 3389,
    max_ips: int = 8_000,
    timeout: float = 0.8,
) -> List[str]:
    """
    Scan CIDR blocks for an open port.
    Returns a list of IPs where the specified port accepted a TCP connection.
    Results are randomised — no ordering guarantee.
    """
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    all_ips: List[str] = []

    for cidr in cidrs:
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            # Skip overly large networks to avoid memory blow-up
            if network.num_addresses > 65536:
                continue
            all_ips.extend(str(h) for h in network.hosts())
            if len(all_ips) >= max_ips * 5:
                break
        except Exception:
            continue

    if not all_ips:
        return []

    random.shuffle(all_ips)
    all_ips = all_ips[:max_ips]

    tasks = [_check_port(ip, port, timeout, semaphore) for ip in all_ips]
    found: List[str] = []
    batch_size = 1_000

    for i in range(0, len(tasks), batch_size):
        results = await asyncio.gather(*tasks[i: i + batch_size])
        found.extend(r for r in results if r is not None)

    return found
