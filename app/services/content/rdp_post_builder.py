"""
RDP Post Builder — single fixed template (THUNDER DROP).
Username is always hardcoded as Administrator.
Image is always the UPGRADE TEAM brand banner (app/assets/rdp_banner.jpg).
"""
from datetime import datetime
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")
FIXED_USERNAME = "Administrator"

# Static brand image — no AI, no external service, no API key needed.
RDP_BANNER_IMAGE = "FILE:app/assets/rdp_banner.jpg"


_DROP_LINES = [
    "\U0001f4a5 Free Windows Server just dropped \u2014 grab it now",
    "\U0001f525 Premium server unlocked \u2014 100% free, no tricks",
    "\U0001f381 Free RDP just dropped \u2014 yours for the taking",
    "\u26a1 Live free server alert \u2014 limited time, act fast",
    "\U0001f4e2 Exclusive drop \u2014 free Windows Server online now",
    "\U0001f30d Free server found \u2014 sharing with the community",
    "\U0001f48e Premium RDP access \u2014 dropped for free today",
    "\U0001f680 Hot drop \u2014 free Windows Server just went live",
    "\U0001f4bb Free server unlocked \u2014 connect before it\u2019s gone",
    "\u2b50 Server giveaway \u2014 full admin access, totally free",
    "\U0001f4e1 Live server drop \u2014 free access for everyone",
    "\U0001f3c6 Big drop \u2014 free RDP server online right now",
]


def _drop_line(seed: int) -> str:
    return _DROP_LINES[seed % len(_DROP_LINES)]


def _now_parts() -> tuple[str, str]:
    now = datetime.now(TEHRAN)
    return now.strftime("%d %b %Y"), now.strftime("%H:%M")


def build_rdp_post(
    ip: str,
    port: int,
    username: str,
    password: str,
    country_name: str,
    country_flag: str,
    seed: int,
) -> tuple[str, str]:
    """
    Build the THUNDER DROP RDP post.
    Username is always Administrator regardless of what is passed.
    Image is always RDP/VPS/Server/VDS themed.
    Returns (post_text, image_urls_string).
    """
    date_str, time_str = _now_parts()

    text = (
        "\u26a1\u26a1 THUNDER DROP \u2014 LIVE FREE RDP \u26a1\u26a1\n"
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
        "\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
        f"{_drop_line(seed)}\n"
        "\U0001f513 Full admin rights \u00b7 Windows Server\n"
        f"\U0001f4cd {country_flag} {country_name} \u00b7 Port {port}\n\n"
        "  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
        "\u2500\u2500\u2510\n"
        f"  \u2502  \U0001f310  {ip}:{port}\n"
        f"  \u2502  \U0001f464  {FIXED_USERNAME}\n"
        f"  \u2502  \U0001f511  {password}\n"
        f"  \u2502  \U0001f7e2  LIVE \u00b7 {date_str}  \u00b7  {time_str}\n"
        "  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
        "\u2500\u2500\u2518\n\n"
        "\U0001f4cb \u2500\u2500\u2500\u2500\u2500\u2500  N O T E  \u2500\u2500\u2500\u2500\u2500\u2500 \U0001f4cb\n"
        "\u26a0\ufe0f  This server\u2019s password rotates automatically\n"
        "    as user capacity fills \u2014 by design.\n"
        "\u23f3  Unable to connect? The next server drops\n"
        "    in exactly \u223c\u202f3 hours on this channel.\n"
        "\U0001f514  Stay subscribed \u00b7 Get every drop first.\n"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500"
        "\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n"
        "\U0001f680 Connect: mstsc \u2192 paste IP \u2192 login\n"
        "\u2705 Works on PC \u00b7 Mac \u00b7 Android \u00b7 iPhone\n\n"
        "\U0001f4cc Save this post \u00b7 Share with friends!\n\n"
        "#ServerDrop #FreeRDP #WindowsFree #RemoteServer #CloudFree\n\n"
        "\U0001f517  @Seller_rdp  \u00b7  Tap to Follow\n\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
        "\u2501\u2501\u2501\n"
        "\U0001f451  Official Admin  |  @VPS24H"
    )

    return text, RDP_BANNER_IMAGE
