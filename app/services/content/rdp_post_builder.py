"""
RDP Post Builder — 10 unique premium templates.
- No channel tag or t.me links (publisher.py handles those)
- Picsum (instant, reliable) + Pollinations.ai (AI-themed) for images
- Admin signature NOT added here — publisher.py handles it for all posts
"""
import random
import urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")

# ── Hashtag pools ─────────────────────────────────────────────────────────
HASHTAG_POOLS = [
    "#FreeRDP #FreeVPS #ServerDrop #RemoteDesktop #FreeServer #Windows",
    "#RDPDrop #VPSFree #FreeAccess #CloudServer #FreeRDP #WindowsServer",
    "#ServerGiveaway #FreeVPS #RemoteAccess #RDPFree #FreeCloud #RDP",
    "#FreeRDPServer #WindowsRDP #ServerAccess #FreeVPS #CloudRDP",
    "#LiveRDP #FreeServer #VPSGiveaway #RDPAccess #FreeWindows",
    "#CyberDrop #FreeRDP #ServerAlert #VPSFree #FreeAccess #RDP2026",
    "#ServerDrop #FreeRDP #WindowsFree #RemoteServer #CloudFree",
    "#FreePremiumRDP #VPSServer #CloudHosting #FreeAccess #RDPServer",
]

# ── Reliable tech images (Picsum — instant CDN, seed-deterministic) ───────
# Combined with Pollinations.ai AI generation as second fallback
_URL_SEPARATOR = "|||"

# Curated Picsum seeds known to return dark/tech-looking photos
_PICSUM_SEEDS = [
    "server01", "datacenter", "tech2026", "cloudnet", "rdpnode",
    "sysadmin", "netgrid", "cyberlab", "hostpro", "vpszone",
    "serverx", "technode", "darklab", "cyborg1", "matrix9",
    "nexuscore", "vpsprime", "rdpvault", "phantom7", "srvdrop",
]

_RDP_PROMPTS = [
    "dramatic server room neon blue glowing racks fog cinematic ultra HD",
    "cyberpunk datacenter rows glowing servers purple light photorealistic",
    "hacker workstation dual monitors green matrix code dark neon aesthetic",
    "digital network visualization glowing data streams deep blue black 8K",
    "premium cloud servers floating cubes dark sky electric blue neon",
    "Windows Remote Desktop ultrawide monitor dark setup dramatic lighting",
    "server rack room red blue LED professional datacenter cinematic",
    "binary code circuit board neon lights 8K digital art dark",
    "global network connections glowing blue nodes dark background tech",
    "massive datacenter night glowing lights dramatic cinematic 4K",
    "command center multiple screens server monitoring dark tech room",
    "fiber optic cables glowing orange blue macro dark datacenter",
    "CPU chip glowing circuits neon blue macro ultra detailed dark 8K",
    "VPN tunnel encrypted data stream neon particles dark tech",
    "RDP server access concept glowing blue server room cinematic",
    "deep space server farm orbital datacenter stars blue nebula 8K",
    "minimalist server room floor reflection professional architecture",
    "digital shield server tower blue energy field cybersecurity art",
    "premium VPS containers floating dark tech 4K render",
    "aerial view datacenter complex night orange blue lights dramatic",
]


def _picsum_url(seed_str: str, w: int = 1200, h: int = 675) -> str:
    return f"https://picsum.photos/seed/{seed_str}/{w}/{h}"


def _pollinations_url(prompt: str, seed: int) -> str:
    encoded = urllib.parse.quote(prompt)
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=960&height=540&model=flux&seed={seed}&nologo=true"
    )


def generate_rdp_image_urls(seed: int) -> str:
    """
    Generate 3 fallback image URLs.
    1st: Picsum (instant CDN — always loads)
    2nd: Pollinations.ai AI image (themed, may take 10-30s)
    3rd: Second Picsum (different seed, instant fallback)
    """
    ps1 = _PICSUM_SEEDS[seed % len(_PICSUM_SEEDS)]
    ps2 = _PICSUM_SEEDS[(seed + 5) % len(_PICSUM_SEEDS)]
    prompt = _RDP_PROMPTS[seed % len(_RDP_PROMPTS)]

    url1 = _picsum_url(ps1)
    url2 = _pollinations_url(prompt, seed)
    url3 = _picsum_url(ps2, 960, 540)

    return f"{url1}{_URL_SEPARATOR}{url2}{_URL_SEPARATOR}{url3}"


def _now() -> str:
    return datetime.now(TEHRAN).strftime("%d %b %Y  \u00b7  %H:%M")


# ─────────────────────────────────────────────────────────────────────────
# Template 1 — SIGNAL INTERCEPTED
# ─────────────────────────────────────────────────────────────────────────
def _t_signal(ip, port, username, password, country_name, country_flag):
    sep  = "\u2500" * 36
    bold = "\u2501" * 36
    return (
        "\U0001f4e1 \u2007SIGNAL INTERCEPTED \u2014 FREE SERVER\n"
        f"{sep}\n\n"
        "\U0001f534 \u2007Target acquired \u00b7 Full Windows admin access\n"
        "\u26a1 \u2007Connection live \u2014 act fast before it's gone\n\n"
        f"{bold}\n"
        f"\U0001f5a5\ufe0f \u2007SERVER  \u27a4  {ip}:{port}\n"
        f"\U0001f464 \u2007USER    \u27a4  {username}\n"
        f"\U0001f511 \u2007PASS    \u27a4  {password}\n"
        f"\U0001f30e \u2007REGION  \u27a4  {country_flag} {country_name}\n"
        f"\u23f1\ufe0f \u2007CAPTURED \u27a4 {_now()}\n"
        f"{bold}\n\n"
        "\U0001f4f2 \u2007HOW TO CONNECT\n"
        "  \u25b6 Windows \u2192 Win+R \u2192 type mstsc \u2192 paste IP\n"
        "  \u25b6 Mac / iOS \u2192 Microsoft Remote Desktop\n"
        "  \u25b6 Android \u2192 RD Client by Microsoft\n\n"
        "\U0001f381 100% Free \u00b7 No sign-up \u00b7 No catch"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 2 — THUNDER DROP
# ─────────────────────────────────────────────────────────────────────────
def _t_thunder(ip, port, username, password, country_name, country_flag):
    dbl = "\u2550" * 36
    return (
        "\u26a1\u26a1 THUNDER DROP \u2014 LIVE FREE RDP \u26a1\u26a1\n"
        f"{dbl}\n\n"
        "\U0001f4a5 Scanner hit a LIVE target \u2014 sharing for free\n"
        "\U0001f513 Full admin rights \u00b7 Windows Server\n"
        f"\U0001f4cd {country_flag} {country_name} \u00b7 Port {port}\n\n"
        "  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510\n"
        f"  \u2502  \U0001f310  {ip}:{port}\n"
        f"  \u2502  \U0001f464  {username}\n"
        f"  \u2502  \U0001f511  {password}\n"
        f"  \u2502  \U0001f7e2  LIVE \u00b7 {_now()}\n"
        "  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n\n"
        "\U0001f680 Connect: mstsc \u2192 paste IP \u2192 login\n"
        "\u2705 Works on PC \u00b7 Mac \u00b7 Android \u00b7 iPhone\n\n"
        "\U0001f4cc Save this post \u00b7 Share with friends!"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 3 — VAULT BREACHED
# ─────────────────────────────────────────────────────────────────────────
def _t_vault(ip, port, username, password, country_name, country_flag):
    sep   = "\u2500" * 40
    thick = "\u2501" * 40
    return (
        "\U0001f513\U0001f3c6 VAULT BREACHED \u2014 FREE ACCESS GRANTED\n"
        f"{sep}\n\n"
        "\U0001f48e Premium Windows Server\n"
        f"\U0001f4b0 Worth \u00a380\u2013120/month \u2014 yours FREE right now\n"
        f"\U0001f4cd {country_flag} {country_name}\n\n"
        f"  \U0001f310 IP    \u203a  {ip}\n"
        f"  \U0001f50c PORT  \u203a  {port}\n"
        f"  \U0001f464 USER  \u203a  {username}\n"
        f"  \U0001f5dd\ufe0f PASS  \u203a  {password}\n"
        f"  \u23f0 TIME  \u203a  {_now()}\n\n"
        f"{thick}\n"
        "\U0001f4f2 CONNECT IN 4 STEPS\n"
        "  \u2460 Open Remote Desktop (mstsc)\n"
        f"  \u2461 Enter  {ip}:{port}\n"
        f"  \u2462 Username: {username}\n"
        f"  \u2463 Password: {password} \u2705\n"
        f"{thick}\n\n"
        "\U0001f680 No registration. No payment. Forever free."
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 4 — PHANTOM SERVER
# ─────────────────────────────────────────────────────────────────────────
def _t_phantom(ip, port, username, password, country_name, country_flag):
    line = "\u2500" * 38
    return (
        "\U0001f47b PHANTOM SERVER \u2014 ZERO-COST ACCESS\n"
        f"{line}\n\n"
        f"\u25c8 Found in the wild \u00b7 Sharing for FREE\n"
        f"\u25c8 {country_flag} {country_name} \u00b7 Port {port} \u00b7 Full Windows Admin\n\n"
        f"{line}\n"
        f"  SERVER  \u2192  {ip}:{port}\n"
        f"  LOGIN   \u2192  {username}\n"
        f"  SECRET  \u2192  {password}\n"
        f"  STATUS  \u2192  \U0001f7e2 ONLINE \u00b7 {_now()}\n"
        f"{line}\n\n"
        "\U0001f576\ufe0f No logs \u00b7 No registration \u00b7 No cost\n"
        "\U0001f4d6 Save it now \u2014 you will need this later"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 5 — NEXUS NODE
# ─────────────────────────────────────────────────────────────────────────
def _t_nexus(ip, port, username, password, country_name, country_flag):
    thick = "\u2501" * 36
    return (
        "\U0001f310 NEXUS NODE ONLINE \u2014 FREE RDP\n"
        f"{thick}\n\n"
        "\U0001f517 New node detected in our network grid\n"
        f"\U0001f4cd {country_flag} {country_name} \u00b7 \U0001f7e2 LIVE\n\n"
        "  \u250c\u2500 ACCESS CREDENTIALS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510\n"
        f"  \u2502  HOST  {ip}:{port}\n"
        f"  \u2502  USER  {username}\n"
        f"  \u2502  PASS  {password}\n"
        "  \u2502  OS    Windows Server \u2014 Full Admin\n"
        f"  \u2502  TIME  {_now()}\n"
        "  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n\n"
        "\U0001f6e0\ufe0f QUICK CONNECT\n"
        "  \u2192 Windows: Run \u00abmstsc\u00bb \u00b7 Enter IP above\n"
        "  \u2192 Mobile: Microsoft RD Client app\n\n"
        "\u2b50 Follow for daily server drops!"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 6 — APEX DROP
# ─────────────────────────────────────────────────────────────────────────
def _t_apex(ip, port, username, password, country_name, country_flag):
    dbl   = "\u2550" * 38
    thick = "\u2501" * 38
    return (
        "\U0001f3c6\U0001f525 APEX DROP \u2014 FREE PREMIUM SERVER\n"
        f"{dbl}\n\n"
        "\U0001f4b0 Market value: ~\u00a380\u2013120 / month\n"
        "\u2705 Your price today: ABSOLUTELY FREE\n"
        f"\U0001f4cd {country_flag} {country_name} \u00b7 Full Admin Access\n\n"
        f"{thick}\n"
        f"  \U0001f5a5\ufe0f  {ip}:{port}\n"
        f"  \U0001f510  {username}  /  {password}\n"
        f"  \u23f0  {_now()}\n"
        f"{thick}\n\n"
        "\u26a1 INSTANT ACCESS \u2014 3 EASY STEPS\n"
        "  1\ufe0f\u20e3 Open mstsc (Windows) or RD Client (mobile)\n"
        f"  2\ufe0f\u20e3 Type  {ip}:{port}\n"
        "  3\ufe0f\u20e3 Enter username & password above \U0001f389\n\n"
        "\U0001f514 Follow for daily free server drops!"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 7 — NOVA LAUNCH
# ─────────────────────────────────────────────────────────────────────────
def _t_nova(ip, port, username, password, country_name, country_flag):
    sep = "\u2500" * 36
    return (
        "\U0001f4ab\U0001f31f NOVA SERVER LAUNCH \u2014 100% FREE\n"
        f"{sep}\n\n"
        "\U0001f31f Brand new \u00b7 Fully clean \u00b7 No tricks ever\n"
        f"\U0001f513 Windows Server \u00b7 {country_flag} {country_name}\n\n"
        "  \u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\n"
        f"  \u2502  \U0001f310 {ip}:{port}\n"
        f"  \u2502  \U0001f464 {username}\n"
        f"  \u2502  \U0001f511 {password}\n"
        f"  \u2502  \U0001f5fa\ufe0f {country_flag} {country_name}\n"
        f"  \u2502  \u23f0 {_now()}\n"
        "  \u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f\n\n"
        "\U0001f4f1 Works on ALL devices\n"
        "  Windows \u00b7 macOS \u00b7 iOS \u00b7 Android\n\n"
        "\u2764\ufe0f Forward to a friend \u00b7 Subscribe for more!"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 8 — SHADOW ACCESS
# ─────────────────────────────────────────────────────────────────────────
def _t_shadow(ip, port, username, password, country_name, country_flag):
    bar = "\u25ac" * 19
    return (
        "\U0001f311\U0001f5a4 SHADOW ACCESS \u2014 FREE WINDOWS SERVER\n"
        f"{bar}\n\n"
        "\U0001f575\ufe0f Dropped by scanner \u00b7 No cost \u00b7 No catch\n"
        f"\u26a1 {country_flag} {country_name} \u00b7 Port {port} \u00b7 LIVE NOW\n\n"
        f"  \u258c SERVER  {ip}\n"
        f"  \u258c PORT    {port}\n"
        f"  \u258c USER    {username}\n"
        f"  \u258c PASS    {password}\n"
        f"  \u258c TIME    {_now()}\n"
        "  \u258c STATUS  \U0001f7e2 ACTIVE\n\n"
        f"{bar}\n\n"
        f"\U0001f517 Connect: mstsc \u2192 {ip}:{port}\n"
        "\U0001f4a1 Use for work, hosting, privacy \u2014 anything\n\n"
        "\U0001f516 Bookmark this \u00b7 More drops every day!"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 9 — TITAN DROP
# ─────────────────────────────────────────────────────────────────────────
def _t_titan(ip, port, username, password, country_name, country_flag):
    thick = "\u2501" * 36
    return (
        "\U0001f531\U0001f4aa TITAN SERVER \u2014 ZERO COST DROP\n"
        f"{thick}\n\n"
        "\U0001f4aa High-power Windows Server \u00b7 Completely free\n"
        f"\U0001f30d Location: {country_flag} {country_name} \u00b7 \U0001f7e2 LIVE & VERIFIED\n\n"
        "  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510\n"
        f"  \u2502  HOST  {ip}:{port}\n"
        f"  \u2502  USER  {username}\n"
        f"  \u2502  PASS  {password}\n"
        f"  \u2502  TIME  {_now()}\n"
        "  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n\n"
        "\u2699\ufe0f STEP-BY-STEP GUIDE\n"
        "  \u2192 Press Win+R \u2192 type mstsc \u2192 hit Enter\n"
        f"  \u2192 Computer: {ip}:{port}\n"
        f"  \u2192 Username: {username}\n"
        f"  \u2192 Password: {password}\n\n"
        "\U0001f680 No registration. No payment. Ever."
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 10 — MATRIX ENTRY
# ─────────────────────────────────────────────────────────────────────────
def _t_matrix(ip, port, username, password, country_name, country_flag):
    shade = "\u2591" * 19
    return (
        "\U0001f4bb\U0001f7e9 MATRIX ENTRY \u2014 FREE SERVER ACCESS\n"
        f"{shade}\n\n"
        "[ SYSTEM BREACH DETECTED ]\n"
        f"[ TARGET: {country_flag} {country_name} \u00b7 PORT {port} ]\n"
        f"[ STATUS: \U0001f7e2 ONLINE \u00b7 ACCESS GRANTED ]\n\n"
        f"  \u25b6 IP      {ip}\n"
        f"  \u25b6 PORT    {port}\n"
        f"  \u25b6 USER    {username}\n"
        f"  \u25b6 PASS    {password}\n"
        f"  \u25b6 TIME    {_now()}\n"
        "  \u25b6 OS      Windows Server \u00b7 Full Admin\n\n"
        f"{shade}\n\n"
        f"\u2328\ufe0f COMMAND: mstsc \u2192 {ip}:{port}\n"
        "\U0001f4f1 MOBILE: Microsoft RD Client app\n\n"
        "\U0001f4be Save this \u00b7 Share this \u00b7 Use it now"
    )


# ─────────────────────────────────────────────────────────────────────────
_TEMPLATES = [
    _t_signal, _t_thunder, _t_vault, _t_phantom, _t_nexus,
    _t_apex,   _t_nova,   _t_shadow, _t_titan,  _t_matrix,
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
    Build an RDP post and 3 image URLs (Picsum + Pollinations fallbacks).
    Template chosen by seed — no consecutive repeats.
    Returns (post_text, image_urls_string).

    NOTE: Admin signature and channel tag are NOT added here.
    publisher.py adds them consistently for all post types.
    """
    template_fn = _TEMPLATES[seed % len(_TEMPLATES)]
    body = template_fn(ip, port, username, password, country_name, country_flag)
    hashtags = random.choice(HASHTAG_POOLS)
    post_text = f"{body}\n\n{hashtags}"
    image_urls = generate_rdp_image_urls(seed)
    return post_text, image_urls
