import asyncio
import ipaddress
import random
from typing import List, Optional

SEMAPHORE_LIMIT = 300


async def _check_port(
    ip: str,
    port: int,
    timeout: float,
    semaphore: asyncio.Semaphore,
) -> Optional[str]:
    async with semaphore:
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=timeout
            )
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return ip
        except Exception:
            return None


async def scan_port(
    cidrs: List[str],
    port: int = 3389,
    max_ips: int = 8_000,
    timeout: float = 1.2,
) -> List[str]:
    """Scan CIDR blocks for an open port. Returns list of IPs with port open."""
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    all_ips: List[str] = []
    for cidr in cidrs:
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            all_ips.extend(str(h) for h in network.hosts())
            if len(all_ips) >= max_ips * 5:
                break
        except Exception:
            continue
    random.shuffle(all_ips)
    all_ips = all_ips[:max_ips]
    if not all_ips:
        return []
    tasks = [_check_port(ip, port, timeout, semaphore) for ip in all_ips]
    found: List[str] = []
    batch = 1_000
    for i in range(0, len(tasks), batch):
        results = await asyncio.gather(*tasks[i : i + batch])
        found.extend(r for r in results if r is not None)
    return found
