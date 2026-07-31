"""
RDP Plans Post Builder — beautiful tree-branch hierarchical layout for Telegram channels.

Each plan is rendered as a branching tree card with emoji-rich specs + price.
Post text is kept under 1024 chars so it sends as a single photo+caption message.
Returns (post_text, image_url) — image reuses the UPGRADE TEAM brand banner.
"""
import random as _random

# ── Plan catalogue — edit prices/specs here ───────────────────────────────────
RDP_PLANS = [
    {
        "icon":  "🌿",
        "badge": "🥈",
        "name":  "PRO",
        "cpu":   "4 vCPU",
        "ram":   "8 GB RAM",
        "disk":  "120 GB SSD",
        "net":   "1 Gbps",
        "price": "$16",
    },
    {
        "icon":  "⚡",
        "badge": "🥇",
        "name":  "POWER",
        "cpu":   "6 vCPU",
        "ram":   "16 GB RAM",
        "disk":  "250 GB SSD",
        "net":   "2 Gbps",
        "price": "$28",
    },
    {
        "icon":  "💠",
        "badge": "💎",
        "name":  "ELITE",
        "cpu":   "8 vCPU",
        "ram":   "32 GB RAM",
        "disk":  "500 GB SSD",
        "net":   "2 Gbps",
        "price": "$45",
    },
    {
        "icon":  "🔱",
        "badge": "🏆",
        "name":  "ULTRA",
        "cpu":   "12 vCPU",
        "ram":   "64 GB RAM",
        "disk":  "1 TB SSD",
        "net":   "5 Gbps",
        "price": "$75",
    },
]

_BANNER_IMAGE = ""  # no image — text-only post

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

_SEP = "━" * 30


def _spaced(name: str) -> str:
    return "  ".join(name)


def _plan_card(p: dict) -> str:
    """Render a single plan as a compact tree-branch card."""
    return "\n".join([
        f"{p['icon']} ┌── {_spaced(p['name'])} ── {p['badge']}",
        f"   ├── 🖥️ CPU  ➜ {p['cpu']}",
        f"   ├── 🧠 RAM  ➜ {p['ram']}",
        f"   ├── 💾 SSD  ➜ {p['disk']}",
        f"   ├── 🌐 NET  ➜ {p['net']}",
        f"   └── 💰 Price ➜ {p['price']} / month",
    ])


def build_rdp_plans_post(
    channel_username: str | None = None,
    seed: int | None = None,
) -> tuple[str, str]:
    if seed is None:
        seed = _random.randint(0, 9_999_999)

    admin_sig = _ADMIN_SIGNATURES[seed % len(_ADMIN_SIGNATURES)]
    cards_txt = "\n\n".join(_plan_card(p) for p in RDP_PLANS)

    tag_line = ""
    if channel_username:
        u   = channel_username.lstrip("@")
        fmt = _CHANNEL_TAG_FORMATS[seed % len(_CHANNEL_TAG_FORMATS)]
        tag_line = fmt.format(u=u) + "\n"

    text = (
        f"{_SEP}\n\n"
        f"{cards_txt}\n\n"
        f"{_SEP}\n\n"
        f"✅ Full RDP Access · Root Admin\n"
        f"✅ Instant Delivery · 24/7 Support\n"
        f"✅ Monthly Billing · Easy Renewal\n"
        f"{tag_line}"
        f"\n{_SEP}\n"
        f"{admin_sig}"
    )

    return text, _BANNER_IMAGE
