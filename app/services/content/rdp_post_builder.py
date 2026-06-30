"""
RDP Post Builder — single fixed template (THUNDER DROP).
Username is always hardcoded as Administrator.
No image is attached; the post is plain text only.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")

FIXED_USERNAME = "Administrator"


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
) -> tuple[str, None]:
    """
    Build the THUNDER DROP RDP post.
    Username is always Administrator regardless of what is passed.
    Returns (post_text, None) — no image.
    """
    date_str, time_str = _now_parts()

    text = (
        "\u26a1\u26a1 THUNDER DROP \u2014 LIVE FREE RDP \u26a1\u26a1\n"
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550"
        "\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
        "\U0001f4a5 Scanner hit a LIVE target \u2014 sharing for free\n"
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

    return text, None
