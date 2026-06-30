import httpx
from typing import List

# Source: https://www.ipdeny.com/ipblocks/data/countries/{cc}.zone
_BASE_URL = "https://www.ipdeny.com/ipblocks/data/countries/{cc}.zone"

# Fallback: aggregated zones (some countries like US have many CIDRs here)
_AGG_URL = "https://www.ipdeny.com/ipblocks/data/aggregated/{cc}-aggregated.zone"


async def get_country_cidr_blocks(country_code: str) -> List[str]:
    """Fetch IPv4 CIDR blocks for a country from ipdeny.com."""
    cc = country_code.lower()
    async with httpx.AsyncClient(timeout=30) as client:
        # Try aggregated first (fewer, cleaner CIDRs)
        for url_tmpl in [_AGG_URL, _BASE_URL]:
            url = url_tmpl.format(cc=cc)
            resp = await client.get(url)
            if resp.status_code == 200 and resp.text.strip():
                cidrs = [
                    line.strip()
                    for line in resp.text.strip().split("\n")
                    if line.strip() and "/" in line
                ]
                if cidrs:
                    return cidrs
        raise ValueError(
            f"No IP ranges found for country code '{cc.upper()}'. "
            "Make sure it's a valid 2-letter ISO code (e.g. US, DE, NL, IR)."
        )
