"""
RDP Post Builder — 10 unique, premium-quality templates for free RDP/VPS/SERVER posts.
Template chosen by seed so consecutive posts never repeat.
Images generated via Pollinations.ai — 3-URL fallback for maximum reliability.
Admin signature is NOT added here; publisher.py handles it for all post types.
"""
import random
import urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")

CHANNEL_TAG  = "@VPS24H"
CHANNEL_LINK = "t.me/VPS24H"

# ── Hashtag pools (8 varied sets) ─────────────────────────────────────────
HASHTAG_POOLS = [
    "#FreeRDP #FreeVPS #ServerDrop #RemoteDesktop #VPS24H #FreeServer #Windows",
    "#RDPDrop #VPSFree #FreeAccess #CloudServer #VPS24H #FreeRDP #WindowsServer",
    "#ServerGiveaway #FreeVPS #RemoteAccess #RDPFree #VPS24H #FreeCloud #RDP",
    "#FreeRDPServer #WindowsRDP #ServerAccess #VPS24H #FreeVPS #CloudRDP",
    "#LiveRDP #FreeServer #VPSGiveaway #RDPAccess #VPS24H #FreeWindows",
    "#CyberDrop #FreeRDP #ServerAlert #VPSFree #VPS24H #FreeAccess #RDP2026",
    "#ServerDrop #FreeRDP #WindowsFree #VPS24H #RemoteServer #CloudFree",
    "#FreePremiumRDP #VPSServer #CloudHosting #FreeAccess #VPS24H #RDPServer",
]

# ── Image prompts (20 cinematic, high-quality prompts) ────────────────────
RDP_IMAGE_PROMPTS = [
    "futuristic dark server room neon blue glowing racks fog dramatic cinematic ultra HD 8K",
    "dramatic datacenter interior rows glowing servers blue purple light photorealistic",
    "cyberpunk hacker workstation dual monitors green matrix code dark neon aesthetic",
    "abstract digital network visualization glowing data streams deep blue black 8K",
    "premium cloud computing floating server cubes dark sky electric blue neon ultra realistic",
    "Windows Remote Desktop ultrawide monitor professional office dark setup dramatic lighting",
    "powerful server rack room red blue LED professional datacenter photography cinematic",
    "binary code circuit board deep blue green neon lights 8K digital art",
    "globe digital network connections glowing blue nodes dark background premium tech",
    "aerial view massive datacenter complex night glowing orange blue lights dramatic cinematic",
    "hacker typing keyboard multiple screens code dark room green amber light moody cinematic",
    "VPN tunnel encrypted data stream neon blue particles dark tech background",
    "RDP server access concept lock unlocking server room blue dramatic light cinematic",
    "premium VPS hosting virtual machine containers floating dark tech 4K render",
    "digital shield protecting server tower blue energy field cybersecurity concept art",
    "deep space server farm orbital datacenter stars blue nebula ultra detailed 8K",
    "fiber optic cables glowing orange blue close up macro dark datacenter background",
    "minimalist server room perfect lighting floor reflection professional architecture photography",
    "CPU chip glowing circuits neon blue purple macro ultra detailed dark background 8K",
    "command center multiple screens server monitoring dark tech room cinematic lighting",
]

_URL_SEPARATOR = "|||"


def _pollinations_url(prompt: str, seed: int, width: int = 1280, height: int = 720) -> str:
    encoded = urllib.parse.quote(prompt)
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}&model=flux&seed={seed}&nologo=true&enhance=true"
    )


def generate_rdp_image_urls(seed: int) -> str:
    """Generate 3 fallback image URLs for maximum reliability."""
    idx1 = seed % len(RDP_IMAGE_PROMPTS)
    idx2 = (seed + 7) % len(RDP_IMAGE_PROMPTS)
    idx3 = (seed + 13) % len(RDP_IMAGE_PROMPTS)
    url1 = _pollinations_url(RDP_IMAGE_PROMPTS[idx1], seed)
    url2 = _pollinations_url(RDP_IMAGE_PROMPTS[idx2], seed + 1)
    url3 = _pollinations_url(RDP_IMAGE_PROMPTS[idx3], seed + 2, 1024, 576)
    return f"{url1}{_URL_SEPARATOR}{url2}{_URL_SEPARATOR}{url3}"


def _now() -> str:
    return datetime.now(TEHRAN).strftime("%d %b %Y  ·  %H:%M")


# ─────────────────────────────────────────────────────────────────────────
# Template 1: SIGNAL
# ─────────────────────────────────────────────────────────────────────────
def _t_signal(ip, port, username, password, country_name, country_flag):
    sep = "─" * 36
    thick = "━" * 36
    return (
        f"U0001f4e1  SIGNAL INTERCEPTED — FREE SERVER
"
        f"{sep}

"
        f"U0001f534  Target acquired. Full Windows access.
"
        f"⚡  Connection live — act fast before it's gone.

"
        f"{thick}
"
        f"U0001f5a5  SERVER    {ip}:{port}
"
        f"U0001f464  USER      {username}
"
        f"U0001f511  PASS      {password}
"
        f"U0001f30d  REGION    {country_flag}  {country_name}
"
        f"⏱  CAPTURED  {_now()}
"
        f"{thick}

"
        f"U0001f4f2  HOW TO CONNECT
"
        f"  Windows  →  Win+R  →  mstsc  →  enter IP
"
        f"  Mac/iOS  →  Microsoft Remote Desktop app
"
        f"  Android  →  RD Client (Microsoft)

"
        f"U0001f381  100% Free · No sign-up · No catch

"
        f"U0001f4e3  {CHANNEL_TAG}  ·  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 2: THUNDER
# ─────────────────────────────────────────────────────────────────────────
def _t_thunder(ip, port, username, password, country_name, country_flag):
    dbl = "═" * 36
    return (
        f"⚡  THUNDER DROP — LIVE FREE RDP
"
        f"{dbl}

"
        f"U0001f4a5  Scanner hit a live target.
"
        f"U0001f513  Full admin rights · Windows Server
"
        f"U0001f4cd  {country_flag}  {country_name}  ·  Port {port}

"
        f"  ┌───────────────────────────────────┐
"
        f"  │  U0001f310  {ip}:{port}
"
        f"  │  U0001f464  {username}
"
        f"  │  U0001f511  {password}
"
        f"  │  U0001f7e2  LIVE  ·  {_now()}
"
        f"  └───────────────────────────────────┘

"
        f"U0001f680  Connect: mstsc → paste IP → login
"
        f"✅  Works on PC · Mac · Android · iPhone

"
        f"U0001f4cc  Save this post · Share with friends!

"
        f"U0001f4e3  {CHANNEL_TAG}  ·  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 3: VAULT
# ─────────────────────────────────────────────────────────────────────────
def _t_vault(ip, port, username, password, country_name, country_flag):
    sep = "─" * 40
    thick = "━" * 40
    return (
        f"U0001f513  VAULT BREACHED — FREE ACCESS GRANTED
"
        f"{sep}

"
        f"U0001f3c6  Premium Windows Server
"
        f"U0001f48e  Worth $80–120/month — yours FREE right now
"
        f"U0001f4cd  {country_flag} {country_name}

"
        f"  U0001f310  IP      ›  {ip}
"
        f"  U0001f50c  PORT    ›  {port}
"
        f"  U0001f464  USER    ›  {username}
"
        f"  U0001f5dd  PASS    ›  {password}
"
        f"  ⏰  TIME    ›  {_now()}

"
        f"{thick}
"
        f"U0001f4f2  CONNECT IN 4 STEPS
"
        f"  ①  Open Remote Desktop (mstsc)
"
        f"  ②  Enter  {ip}:{port}
"
        f"  ③  Username: {username}
"
        f"  ④  Password: {password}  ✅
"
        f"{thick}

"
        f"U0001f4e3  {CHANNEL_TAG}  ·  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 4: PHANTOM
# ─────────────────────────────────────────────────────────────────────────
def _t_phantom(ip, port, username, password, country_name, country_flag):
    line = "─" * 38
    return (
        f"U0001f441  PHANTOM SERVER — ZERO-COST ENTRY
"
        f"{line}

"
        f"◈  Found in the wild · Sharing for free
"
        f"◈  {country_flag} {country_name}  ·  Port {port}  ·  Full Windows

"
        f"{line}
"
        f"  SERVER  →  {ip}:{port}
"
        f"  LOGIN   →  {username}
"
        f"  SECRET  →  {password}
"
        f"  STATUS  →  U0001f7e2 ONLINE  ·  {_now()}
"
        f"{line}

"
        f"U0001f576  No logs · No registration · No cost
"
        f"U0001f4d6  Save this · You will need it later

"
        f"U0001f4e3  {CHANNEL_TAG}  ·  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 5: NEXUS
# ─────────────────────────────────────────────────────────────────────────
def _t_nexus(ip, port, username, password, country_name, country_flag):
    thick = "━" * 36
    return (
        f"U0001f310  NEXUS NODE ONLINE — FREE RDP
"
        f"{thick}

"
        f"U0001f517  New node detected in our network grid
"
        f"U0001f4cd  {country_flag} {country_name}  ·  U0001f7e2 LIVE

"
        f"  ┌─ ACCESS CREDENTIALS ────────────────┐
"
        f"  │  HOST  {ip}:{port}
"
        f"  │  USER  {username}
"
        f"  │  PASS  {password}
"
        f"  │  OS    Windows Server — Full Admin
"
        f"  │  TIME  {_now()}
"
        f"  └───────────────────────────────────┘

"
        f"U0001f6e0  QUICK CONNECT
"
        f"  →  Windows: Run «mstsc» · Enter IP above
"
        f"  →  Mobile:  Microsoft RD Client app

"
        f"⭐  Like & save · More drops every day!

"
        f"U0001f4e3  {CHANNEL_TAG}  ·  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 6: APEX
# ─────────────────────────────────────────────────────────────────────────
def _t_apex(ip, port, username, password, country_name, country_flag):
    dbl = "═" * 38
    thick = "━" * 38
    return (
        f"U0001f3c6  APEX DROP — FREE PREMIUM SERVER
"
        f"{dbl}

"
        f"U0001f4b0  Market value: ~$80–120 / month
"
        f"✅  Your price today: ABSOLUTELY FREE
"
        f"U0001f4cd  {country_flag} {country_name}  ·  Full Admin Access

"
        f"{thick}
"
        f"  U0001f5a5  {ip}:{port}
"
        f"  U0001f510  {username}  /  {password}
"
        f"  U0001f550  {_now()}
"
        f"{thick}

"
        f"⚡  INSTANT ACCESS — 3 EASY STEPS
"
        f"  1️⃣  Open mstsc (Windows) or RD Client (mobile)
"
        f"  2️⃣  Type  {ip}:{port}
"
        f"  3️⃣  Enter username & password above  U0001f389

"
        f"U0001f514  Follow for daily free server drops!

"
        f"U0001f4e3  {CHANNEL_TAG}  ·  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 7: NOVA
# ─────────────────────────────────────────────────────────────────────────
def _t_nova(ip, port, username, password, country_name, country_flag):
    sep = "─" * 36
    return (
        f"U0001f4ab  NOVA SERVER LAUNCH — 100% FREE
"
        f"{sep}

"
        f"U0001f31f  Brand new · Fully clean · No tricks
"
        f"U0001f513  Windows Server · {country_flag} {country_name}

"
        f"  ╭─────────────────────────────────╮
"
        f"  │  U0001f310  {ip}:{port}
"
        f"  │  U0001f464  {username}
"
        f"  │  U0001f511  {password}
"
        f"  │  U0001f5fa  {country_flag} {country_name}
"
        f"  │  ⏰  {_now()}
"
        f"  ╰─────────────────────────────────╯

"
        f"U0001f4f1  Works on ALL devices
"
        f"  Windows · macOS · iOS · Android

"
        f"❤️  Forward to a friend · Subscribe for more!

"
        f"U0001f4e3  {CHANNEL_TAG}  ·  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 8: SHADOW
# ─────────────────────────────────────────────────────────────────────────
def _t_shadow(ip, port, username, password, country_name, country_flag):
    bar = "▬" * 18
    return (
        f"U0001f311  SHADOW ACCESS — FREE WINDOWS SERVER
"
        f"{bar}

"
        f"U0001f575  Dropped by scanner · No cost · No catch
"
        f"⚡  {country_flag} {country_name}  ·  Port {port}  ·  LIVE NOW

"
        f"  ▌  SERVER  {ip}
"
        f"  ▌  PORT    {port}
"
        f"  ▌  USER    {username}
"
        f"  ▌  PASS    {password}
"
        f"  ▌  TIME    {_now()}
"
        f"  ▌  STATUS  U0001f7e2 ACTIVE

"
        f"{bar}

"
        f"U0001f517  Connect: mstsc → {ip}:{port}
"
        f"U0001f4a1  Use it for work, hosting, privacy — anything

"
        f"U0001f516  Bookmark this channel · Drops every day!

"
        f"U0001f4e3  {CHANNEL_TAG}  ·  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 9: TITAN
# ─────────────────────────────────────────────────────────────────────────
def _t_titan(ip, port, username, password, country_name, country_flag):
    thick = "━" * 36
    return (
        f"U0001f531  TITAN SERVER — ZERO COST DROP
"
        f"{thick}

"
        f"U0001f4aa  High-power Windows Server · Completely free
"
        f"U0001f30d  Location: {country_flag} {country_name}  ·  U0001f7e2 LIVE & VERIFIED

"
        f"  ┌───────────────────────────────────┐
"
        f"  │  HOST  {ip}:{port}
"
        f"  │  USER  {username}
"
        f"  │  PASS  {password}
"
        f"  │  TIME  {_now()}
"
        f"  └───────────────────────────────────┘

"
        f"⚙️  STEP-BY-STEP GUIDE
"
        f"  →  Press Win+R  →  type mstsc  →  hit Enter
"
        f"  →  Computer:  {ip}:{port}
"
        f"  →  Username:  {username}
"
        f"  →  Password:  {password}

"
        f"U0001f680  No registration. No payment. Ever.

"
        f"U0001f4e3  {CHANNEL_TAG}  ·  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 10: MATRIX
# ─────────────────────────────────────────────────────────────────────────
def _t_matrix(ip, port, username, password, country_name, country_flag):
    shade = "░" * 18
    return (
        f"U0001f4bb  MATRIX ENTRY — FREE SERVER ACCESS
"
        f"{shade}

"
        f"[ SYSTEM BREACH DETECTED ]
"
        f"[ TARGET: {country_flag} {country_name}  ·  PORT {port} ]
"
        f"[ STATUS: U0001f7e2 ONLINE  ·  ACCESS GRANTED ]

"
        f"  ▶  IP       {ip}
"
        f"  ▶  PORT     {port}
"
        f"  ▶  USER     {username}
"
        f"  ▶  PASS     {password}
"
        f"  ▶  TIME     {_now()}
"
        f"  ▶  OS       Windows Server · Full Admin

"
        f"{shade}

"
        f"⌨️  COMMAND: mstsc → {ip}:{port}
"
        f"U0001f4f1  MOBILE:  Microsoft RD Client app

"
        f"U0001f4be  Save this · Share this · Use it

"
        f"U0001f4e3  {CHANNEL_TAG}  ·  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
_TEMPLATES = [
    _t_signal,
    _t_thunder,
    _t_vault,
    _t_phantom,
    _t_nexus,
    _t_apex,
    _t_nova,
    _t_shadow,
    _t_titan,
    _t_matrix,
]


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
    Build an attractive RDP post text and 3 fallback image URLs.
    Template chosen by seed — consecutive posts never look the same.
    Returns (post_text, image_urls_string).

    NOTE: Admin signature is NOT included here.
    publisher.py adds it consistently for all post types — no double-signing.
    """
    template_fn = _TEMPLATES[seed % len(_TEMPLATES)]
    body = template_fn(ip, port, username, password, country_name, country_flag)
    hashtags = random.choice(HASHTAG_POOLS)
    post_text = f"{body}\n\n{hashtags}"
    image_urls = generate_rdp_image_urls(seed)
    return post_text, image_urls
