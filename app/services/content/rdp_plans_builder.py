"""
RDP Plans Post Builder — premium pricing-card layout for Telegram channels.

Inline URL buttons are attached by the publisher/handler. Each plan is rendered
as a bordered card with specs + price.
Returns (post_text, image_url) — image reuses the UPGRADE TEAM brand banner.
"""
import random as _random

# ── Plan catalogue — edit prices/specs here ───────────────────────────────────
RDP_PLANS = [
    {
        "badge": "🥈",
        "name": "PRO",
        "cpu":  "4 vCPU",
        "ram":  "8 GB RAM",
        "disk": "120 GB SSD",
        "net":  "1 Gbps",
        "price": "$16",
    },
    {
        "badge": "🥇",
        "name": "POWER",
        "cpu":  "6 vCPU",
        "ram":  "16 GB RAM",
        "disk": "250 GB SSD",
        "net":  "2 Gbps",
        "price": "$28",
    },
    {
        "badge": "💎",
        "name": "ELITE",
        "cpu":  "8 vCPU",
        "ram":  "32 GB RAM",
        "disk": "500 GB SSD",
        "net":  "2 Gbps",
        "price": "$45",
    },
    {
        "badge": "🔥",
        "name": "ULTRA",
        "cpu":  "12 vCPU",
        "ram":  "64 GB RAM",
        "disk": "1 TB SSD",
        "net":  "5 Gbps",
        "price": "$75",
    },
]

_BANNER_IMAGE = "FILE:app/assets/rdp_banner.jpg"

_HEADLINES = [
    ("🖥  W I N D O W S   R D P  🖥", "⚡  P R E M I U M   P L A N S"),
    ("💻  R D P   V P S   S E R V E R S  💻", "🌟  B E S T   P R I C E S"),
    ("⚡  W I N D O W S   V P S  ⚡", "🚀  P R E M I U M   H O S T I N G"),
    ("🚀  R E M O T E   D E S K T O P  🚀", "💎  V P S   P L A N S"),
    ("🌐  W I N D O W S   S E R V E R  🌐", "🔥  V P S   P R I C I N G"),
]

_CHANNEL_TAG_FORMATS = [
    "📢  @{u}  —  Join Our Channel",
    "📡  @{u}  |  Official Channel",
    "🔔  @{u}  ·  Subscribe Now",
    "💬  @{u}  —  Our Community",
    "🌐  @{u}  |  Follow Us",
    "⭐  @{u}  ·  Stay Updated",
]

_ADMIN_SIGNATURES = [
    "💎  Senior Admin  |  @VPS24H",
    "👑  Official Admin  ›  @VPS24H",
    "🛡️  Head of Operations  ›  @VPS24H",
    "⚜️  Verified Admin  ·  @VPS24H",
    "🔱  Director & Admin  ›  @VPS24H",
    "⚡  Chief Admin  |  @VPS24H",
    "🌟  Verified Publisher  ·  @VPS24H",
    "🏆  Authorized Admin  ·  @VPS24H",
    "🔐  Certified Admin  ›  @VPS24H",
    "📡  Admin & Publisher  |  @VPS24H",
]

_THICK_SEP = "═" * 38
_PLAN_SEP  = "┄" * 38


def _spaced(name: str) -> str:
    """Return 'PRO' → 'P R O' for premium look."""
    return "  ".join(name)


def _plan_card(p: dict) -> str:
    badge = p["badge"]
    name  = _spaced(p["name"])
    cpu   = p["cpu"]
    ram   = p["ram"]
    disk  = p["disk"]
    net   = p["net"]
    price = p["price"]

    return (
        f"◈ {badge}  {name}\n"
        f"┣ 💻  {cpu:<10}  🧠  {ram}\n"
        f"┣ 💾  {disk:<12}  🌐  {net}\n"
        f"┗━ 💰  {price} / month"
    )


def build_rdp_plans_post(
    channel_username: str | None = None,
    seed: int | None = None,
) -> tuple[str, str]:
    """
    Build the RDP plans channel post.
    Returns (post_text, image_url).
    """
    if seed is None:
        seed = _random.randint(0, 9_999_999)

    h1, h2    = _HEADLINES[seed % len(_HEADLINES)]
    admin_sig = _ADMIN_SIGNATURES[seed % len(_ADMIN_SIGNATURES)]

    cards_txt = f"\n{_PLAN_SEP}\n".join(_plan_card(p) for p in RDP_PLANS)

    tag_line = ""
    if channel_username:
        u   = channel_username.lstrip("@")
        fmt = _CHANNEL_TAG_FORMATS[seed % len(_CHANNEL_TAG_FORMATS)]
        tag_line = fmt.format(u=u) + "\n"

    text = (
        f"⚡{_THICK_SEP}⚡\n"
        f"   {h1}\n"
        f"    {h2}\n"
        f"⚡{_THICK_SEP}⚡\n\n"
        "🔐  Full Admin  ·  Windows 2019 / 2022\n"
        "⚡  KVM  ·  NVMe SSD  ·  99.9% Uptime\n"
        "🌍  EU / US  ·  DDoS Protected\n\n"
        f"{_THICK_SEP}\n\n"
        f"{cards_txt}\n\n"
        f"{_THICK_SEP}\n\n"
        "✅  Full RDP Access  ·  Root Admin\n"
        "✅  Windows Server 2019 / 2022\n"
        "✅  Instant Delivery  ·  24/7 Support\n"
        "✅  Monthly Billing  ·  Easy Renewal\n\n"
        f"{tag_line}"
        f"{_THICK_SEP}\n"
        f"{admin_sig}"
    )

    return text, _BANNER_IMAGE
