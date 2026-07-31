"""
    Flash Sale Post Builder - time-limited discount post for RDP plans.
    Returns (post_text, image_url).
    """
    import random as _random
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    TEHRAN = ZoneInfo("Asia/Tehran")

    _PLANS = [
      {"icon": "\U0001f331", "badge": "\U0001f948", "name": "PRO",   "tier": "Entry Level", "cpu": "4 vCPU",  "ram": "8 GB RAM",  "disk": "120 GB SSD", "net": "1 Gbps", "price": 16},
      {"icon": "\u26a1",     "badge": "\U0001f947", "name": "POWER", "tier": "Standard",    "cpu": "6 vCPU",  "ram": "16 GB RAM", "disk": "250 GB SSD", "net": "2 Gbps", "price": 28},
      {"icon": "\U0001f4a0", "badge": "\U0001f48e", "name": "ELITE", "tier": "Advanced",    "cpu": "8 vCPU",  "ram": "32 GB RAM", "disk": "500 GB SSD", "net": "2 Gbps", "price": 45},
      {"icon": "\U0001f531", "badge": "\U0001f3c6", "name": "ULTRA", "tier": "Ultimate",    "cpu": "12 vCPU", "ram": "64 GB RAM", "disk": "1 TB SSD",   "net": "5 Gbps", "price": 75},
    ]

    _DISCOUNTS = [20, 25, 30]

    _ADMIN_SIGNATURES = [
      "\U0001f4ae Senior Admin | @VPS24H",
      "\U0001f451 Official Admin \u203a @VPS24H",
      "\u26a1 Chief Admin | @VPS24H",
      "\U0001f531 Director & Admin \u203a @VPS24H",
      "\u269c\ufe0f Verified Admin \u00b7 @VPS24H",
    ]

    _SEP = "\u2501" * 30


    def _spaced(name: str) -> str:
      return "  ".join(name)


    def _sale_card(p: dict, discount: int) -> str:
      orig = p["price"]
      sale = round(orig * (1 - discount / 100))
      name_spaced = _spaced(p["name"])
      lines = [
          p["icon"] + " \u250c\u2500\u2500 " + name_spaced + " \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 " + p["badge"],
          "   \u251c\u2500\u2500 \U0001f5a5\ufe0f  Processor \u2192 " + p["cpu"],
          "   \u251c\u2500\u2500 \U0001f9e0  Memory    \u2192 " + p["ram"],
          "   \u251c\u2500\u2500 \U0001f4be  Storage   \u2192 " + p["disk"],
          "   \u251c\u2500\u2500 \U0001f310  Network   \u2192 " + p["net"],
          "   \u251c\u2500\u2500 \U0001f3f7\ufe0f  Tier      \u2192 " + p["tier"],
          "   \u251c\u2500\u2500 \U0001f4b8  Was       \u2192 $" + str(orig) + " / month",
          "   \u2514\u2500\u2500 \U0001f4b0  NOW       \u2192 $" + str(sale) + " / month  \U0001f525 -" + str(discount) + "%",
      ]
      return "\n".join(lines)


    def build_flash_sale_post(
      channel_username: str | None = None,
      seed: int | None = None,
      duration_hours: int = 2,
    ) -> tuple[str, str]:
      """Build a timed flash-sale post. Returns (text, image_url)."""
      if seed is None:
          seed = _random.randint(0, 9_999_999)

      discount = _DISCOUNTS[seed % len(_DISCOUNTS)]
      admin_sig = _ADMIN_SIGNATURES[seed % len(_ADMIN_SIGNATURES)]

      now_tehran = datetime.now(TEHRAN)
      expires_at = now_tehran + timedelta(hours=duration_hours)
      expires_str = expires_at.strftime("%H:%M")

      cards_txt = "\n\n".join(_sale_card(p, discount) for p in _PLANS)

      tag_line = ""
      if channel_username:
          u = channel_username.lstrip("@")
          tag_line = "\n\U0001f4e2 @" + u + " \u2014 Join for more deals"

      text = (
          "\u26a1 F L A S H   S A L E \u26a1\n"
          + _SEP + "\n\n"
          + "\U0001f525 LIMITED TIME \u2014 " + str(duration_hours) + " HOURS ONLY\n"
          + "\u23f0 Expires: " + expires_str + " (Tehran Time)\n\n"
          + cards_txt + "\n\n"
          + _SEP + "\n\n"
          + "\u2705 Full RDP Access \u00b7 Root Admin\n"
          + "\u2705 Instant Delivery \u00b7 24/7 Support\n"
          + "\u2705 Monthly Billing \u00b7 Easy Renewal\n"
          + "\U0001f4f2 DM @VPS24H to claim your discount"
          + tag_line + "\n"
          + _SEP + "\n"
          + admin_sig
      )

      return text, ""
    