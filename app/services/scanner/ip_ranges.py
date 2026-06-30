import httpx
  from typing import List


  async def get_country_cidr_blocks(country_code: str) -> List[str]:
      """Fetch IPv4 CIDR blocks for a country from herrbischoff/country-ip-blocks."""
      cc = country_code.lower()
      url = (
          "https://raw.githubusercontent.com/herrbischoff/"
          f"country-ip-blocks/master/ipv4/{cc}.cidr"
      )
      async with httpx.AsyncClient(timeout=30) as client:
          resp = await client.get(url)
          if resp.status_code == 404:
              raise ValueError(f"Unknown country code: {cc.upper()}")
          resp.raise_for_status()
          cidrs = [
              line.strip()
              for line in resp.text.strip().split("\n")
              if line.strip()
          ]
      return cidrs
  