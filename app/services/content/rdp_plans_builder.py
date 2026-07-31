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

_BANNER_IMAGE = "FILE:app/assets/upgrade_team_banner.jpg"

_HEADLINES = [
    ("🖥  W I N D O W S   R D P  🖥", "⚡  P R E M I U M   P L A N S"),
    ("💻  R D P   V P S   S E R V E R S  💻", "🌟  B E S T   P R I C E S"),
    ("⚡  W I N D O W S   V P S  ⚡", "🚀  P R E M I U M   H O S T I N G"),
    ("🚀  R E M O T E   D E S K T O P  🚀", "💎  V P S   P L A N S"),
    ("🌐  W I N D O W S   S E R V E R  🌐", "🔥  V P S   P R I C I N G"),
]

_CHANNEL_TAG_FORMATS = [
    "📢 @{u} — Join Our Channel",
    "📡 @{u} | Official Channel",
    "🔔 @{u} · Subscribe Now",
    "🌐 @{u} | Follow Us",
    "⭐ @{u} · Stay Updated",
]

_ADMIN_SIGNATURES = [
    "💎 Senior Admin | @VPS24H",
    "👑 Official Admin › @VPS24H",
    "🛡️ Head of Operations › @VPS24H",
    "⚜️ Verified Admin · @VPS24H",
    "🔱 Director & Admin › @VPS24H",
    "⚡ Chief Admin | @VPS24H",
    "🌟 Verified Publisher · @VPS24H",
    "🏆 Authorized Admin · @VPS24H",
    "🔐 Certified Admin › @VPS24H",
    "📡 Admin & Publisher | @VPS24H",
]

_SEP   = "━" * 36
_THIN  = "┄" * 36


def _spaced(name: str) -> str:
    return "  ".join(name)


def _plan_card(p: dict) -> str:
    return (
        f"◈ {p['badge']}  {_spaced(p['name'])}\n"
        f"┣ 💻 {p['cpu']:<10} 🧠 {p['ram']}\n"
        f"┣ 💾 {p['disk']:<12} 🌐 {p['net']}\n"
        f"┗━ 💰 {p['price']} / month"
    )


def build_rdp_plans_post(
    channel_username: str | None = None,
    seed: int | None = None,
) -> tuple[str, str]:
    if seed is None:
        seed = _random.randint(0, 9_999_999)

    h1, h2    = _HEADLINES[seed % len(_HEADLINES)]
    admin_sig = _ADMIN_SIGNATURES[seed % len(_ADMIN_SIGNATURES)]
    cards_txt = f"\n{_THIN}\n".join(_plan_card(p) for p in RDP_PLANS)

    tag_line = ""
    if channel_username:
        u   = channel_username.lstrip("@")
        fmt = _CHANNEL_TAG_FORMATS[seed % len(_CHANNEL_TAG_FORMATS)]
        tag_line = fmt.format(u=u) + "\n"

    text = (
        f"⚡{_SEP}⚡\n"
        f"  {h1}\n"
        f"   {h2}\n"
        f"⚡{_SEP}⚡\n"
        f"🔐 Full Admin · Windows 2019/2022\n"
        f"⚡ KVM · NVMe SSD · 99.9% Uptime\n"
        f"🌍 EU/US · DDoS Protected\n"
        f"{_SEP}\n"
        f"{cards_txt}\n"
        f"{_SEP}\n"
        f"✅ Full RDP Access · Root Admin\n"
        f"✅ Instant Delivery · 24/7 Support\n"
        f"✅ Monthly Billing · Easy Renewal\n"
        f"{tag_line}"
        f"{_SEP}\n"
        f"{admin_sig}"
    )

    return text, _BANNER_IMAGE
