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
    return datetime.now(TEHRAN).strftime("%d %b %Y  \u00b7  %H:%M")


# ─────────────────────────────────────────────────────────────────────────
# Template 1: SIGNAL
# ─────────────────────────────────────────────────────────────────────────
def _t_signal(ip, port, username, password, country_name, country_flag):
    sep = "\u2500" * 36
    thick = "\u2501" * 36
    return (
        "\U0001f4e1  SIGNAL INTERCEPTED \u2014 FREE SERVER\n"
        f"{sep}\n\n"
        "\U0001f534  Target acquired. Full Windows access.\n"
        "\u26a1  Connection live \u2014 act fast before it's gone.\n\n"
        f"{thick}\n"
        f"\U0001f5a5  SERVER    {ip}:{port}\n"
        f"\U0001f464  USER      {username}\n"
        f"\U0001f511  PASS      {password}\n"
        f"\U0001f30d  REGION    {country_flag}  {country_name}\n"
        f"\u23f1  CAPTURED  {_now()}\n"
        f"{thick}\n\n"
        "\U0001f4f2  HOW TO CONNECT\n"
        "  Windows  \u2192  Win+R  \u2192  mstsc  \u2192  enter IP\n"
        "  Mac/iOS  \u2192  Microsoft Remote Desktop app\n"
        "  Android  \u2192  RD Client (Microsoft)\n\n"
        "\U0001f381  100% Free \u00b7 No sign-up \u00b7 No catch\n\n"
        f"\U0001f4e3  {CHANNEL_TAG}  \u00b7  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 2: THUNDER
# ─────────────────────────────────────────────────────────────────────────
def _t_thunder(ip, port, username, password, country_name, country_flag):
    dbl = "\u2550" * 36
    return (
        "\u26a1  THUNDER DROP \u2014 LIVE FREE RDP\n"
        f"{dbl}\n\n"
        "\U0001f4a5  Scanner hit a live target.\n"
        "\U0001f513  Full admin rights \u00b7 Windows Server\n"
        f"\U0001f4cd  {country_flag}  {country_name}  \u00b7  Port {port}\n\n"
        "  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510\n"
        f"  \u2502  \U0001f310  {ip}:{port}\n"
        f"  \u2502  \U0001f464  {username}\n"
        f"  \u2502  \U0001f511  {password}\n"
        f"  \u2502  \U0001f7e2  LIVE  \u00b7  {_now()}\n"
        "  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n\n"
        "\U0001f680  Connect: mstsc \u2192 paste IP \u2192 login\n"
        "\u2705  Works on PC \u00b7 Mac \u00b7 Android \u00b7 iPhone\n\n"
        "\U0001f4cc  Save this post \u00b7 Share with friends!\n\n"
        f"\U0001f4e3  {CHANNEL_TAG}  \u00b7  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 3: VAULT
# ─────────────────────────────────────────────────────────────────────────
def _t_vault(ip, port, username, password, country_name, country_flag):
    sep = "\u2500" * 40
    thick = "\u2501" * 40
    return (
        "\U0001f513  VAULT BREACHED \u2014 FREE ACCESS GRANTED\n"
        f"{sep}\n\n"
        "\U0001f3c6  Premium Windows Server\n"
        "\U0001f48e  Worth $80\u2013120/month \u2014 yours FREE right now\n"
        f"\U0001f4cd  {country_flag} {country_name}\n\n"
        f"  \U0001f310  IP      \u203a  {ip}\n"
        f"  \U0001f50c  PORT    \u203a  {port}\n"
        f"  \U0001f464  USER    \u203a  {username}\n"
        f"  \U0001f5dd  PASS    \u203a  {password}\n"
        f"  \u23f0  TIME    \u203a  {_now()}\n\n"
        f"{thick}\n"
        "\U0001f4f2  CONNECT IN 4 STEPS\n"
        "  \u2460  Open Remote Desktop (mstsc)\n"
        f"  \u2461  Enter  {ip}:{port}\n"
        f"  \u2462  Username: {username}\n"
        f"  \u2463  Password: {password}  \u2705\n"
        f"{thick}\n\n"
        f"\U0001f4e3  {CHANNEL_TAG}  \u00b7  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 4: PHANTOM
# ─────────────────────────────────────────────────────────────────────────
def _t_phantom(ip, port, username, password, country_name, country_flag):
    line = "\u2500" * 38
    return (
        "\U0001f441  PHANTOM SERVER \u2014 ZERO-COST ENTRY\n"
        f"{line}\n\n"
        f"\u25c8  Found in the wild \u00b7 Sharing for free\n"
        f"\u25c8  {country_flag} {country_name}  \u00b7  Port {port}  \u00b7  Full Windows\n\n"
        f"{line}\n"
        f"  SERVER  \u2192  {ip}:{port}\n"
        f"  LOGIN   \u2192  {username}\n"
        f"  SECRET  \u2192  {password}\n"
        f"  STATUS  \u2192  \U0001f7e2 ONLINE  \u00b7  {_now()}\n"
        f"{line}\n\n"
        "\U0001f576  No logs \u00b7 No registration \u00b7 No cost\n"
        "\U0001f4d6  Save this \u00b7 You will need it later\n\n"
        f"\U0001f4e3  {CHANNEL_TAG}  \u00b7  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 5: NEXUS
# ─────────────────────────────────────────────────────────────────────────
def _t_nexus(ip, port, username, password, country_name, country_flag):
    thick = "\u2501" * 36
    return (
        "\U0001f310  NEXUS NODE ONLINE \u2014 FREE RDP\n"
        f"{thick}\n\n"
        "\U0001f517  New node detected in our network grid\n"
        f"\U0001f4cd  {country_flag} {country_name}  \u00b7  \U0001f7e2 LIVE\n\n"
        "  \u250c\u2500 ACCESS CREDENTIALS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510\n"
        f"  \u2502  HOST  {ip}:{port}\n"
        f"  \u2502  USER  {username}\n"
        f"  \u2502  PASS  {password}\n"
        "  \u2502  OS    Windows Server \u2014 Full Admin\n"
        f"  \u2502  TIME  {_now()}\n"
        "  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n\n"
        "\U0001f6e0  QUICK CONNECT\n"
        "  \u2192  Windows: Run \u00abmstsc\u00bb \u00b7 Enter IP above\n"
        "  \u2192  Mobile:  Microsoft RD Client app\n\n"
        "\u2b50  Like & save \u00b7 More drops every day!\n\n"
        f"\U0001f4e3  {CHANNEL_TAG}  \u00b7  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 6: APEX
# ─────────────────────────────────────────────────────────────────────────
def _t_apex(ip, port, username, password, country_name, country_flag):
    dbl = "\u2550" * 38
    thick = "\u2501" * 38
    return (
        "\U0001f3c6  APEX DROP \u2014 FREE PREMIUM SERVER\n"
        f"{dbl}\n\n"
        "\U0001f4b0  Market value: ~$80\u2013120 / month\n"
        "\u2705  Your price today: ABSOLUTELY FREE\n"
        f"\U0001f4cd  {country_flag} {country_name}  \u00b7  Full Admin Access\n\n"
        f"{thick}\n"
        f"  \U0001f5a5  {ip}:{port}\n"
        f"  \U0001f510  {username}  /  {password}\n"
        f"  \U0001f550  {_now()}\n"
        f"{thick}\n\n"
        "\u26a1  INSTANT ACCESS \u2014 3 EASY STEPS\n"
        "  1\ufe0f\u20e3  Open mstsc (Windows) or RD Client (mobile)\n"
        f"  2\ufe0f\u20e3  Type  {ip}:{port}\n"
        "  3\ufe0f\u20e3  Enter username & password above  \U0001f389\n\n"
        "\U0001f514  Follow for daily free server drops!\n\n"
        f"\U0001f4e3  {CHANNEL_TAG}  \u00b7  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 7: NOVA
# ─────────────────────────────────────────────────────────────────────────
def _t_nova(ip, port, username, password, country_name, country_flag):
    sep = "\u2500" * 36
    return (
        "\U0001f4ab  NOVA SERVER LAUNCH \u2014 100% FREE\n"
        f"{sep}\n\n"
        "\U0001f31f  Brand new \u00b7 Fully clean \u00b7 No tricks\n"
        f"\U0001f513  Windows Server \u00b7 {country_flag} {country_name}\n\n"
        "  \u256d\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256e\n"
        f"  \u2502  \U0001f310  {ip}:{port}\n"
        f"  \u2502  \U0001f464  {username}\n"
        f"  \u2502  \U0001f511  {password}\n"
        f"  \u2502  \U0001f5fa  {country_flag} {country_name}\n"
        f"  \u2502  \u23f0  {_now()}\n"
        "  \u2570\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u256f\n\n"
        "\U0001f4f1  Works on ALL devices\n"
        "  Windows \u00b7 macOS \u00b7 iOS \u00b7 Android\n\n"
        "\u2764\ufe0f  Forward to a friend \u00b7 Subscribe for more!\n\n"
        f"\U0001f4e3  {CHANNEL_TAG}  \u00b7  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 8: SHADOW
# ─────────────────────────────────────────────────────────────────────────
def _t_shadow(ip, port, username, password, country_name, country_flag):
    bar = "\u25ac" * 18
    return (
        "\U0001f311  SHADOW ACCESS \u2014 FREE WINDOWS SERVER\n"
        f"{bar}\n\n"
        "\U0001f575  Dropped by scanner \u00b7 No cost \u00b7 No catch\n"
        f"\u26a1  {country_flag} {country_name}  \u00b7  Port {port}  \u00b7  LIVE NOW\n\n"
        f"  \u258c  SERVER  {ip}\n"
        f"  \u258c  PORT    {port}\n"
        f"  \u258c  USER    {username}\n"
        f"  \u258c  PASS    {password}\n"
        f"  \u258c  TIME    {_now()}\n"
        "  \u258c  STATUS  \U0001f7e2 ACTIVE\n\n"
        f"{bar}\n\n"
        f"\U0001f517  Connect: mstsc \u2192 {ip}:{port}\n"
        "\U0001f4a1  Use it for work, hosting, privacy \u2014 anything\n\n"
        "\U0001f516  Bookmark this channel \u00b7 Drops every day!\n\n"
        f"\U0001f4e3  {CHANNEL_TAG}  \u00b7  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 9: TITAN
# ─────────────────────────────────────────────────────────────────────────
def _t_titan(ip, port, username, password, country_name, country_flag):
    thick = "\u2501" * 36
    return (
        "\U0001f531  TITAN SERVER \u2014 ZERO COST DROP\n"
        f"{thick}\n\n"
        "\U0001f4aa  High-power Windows Server \u00b7 Completely free\n"
        f"\U0001f30d  Location: {country_flag} {country_name}  \u00b7  \U0001f7e2 LIVE & VERIFIED\n\n"
        "  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510\n"
        f"  \u2502  HOST  {ip}:{port}\n"
        f"  \u2502  USER  {username}\n"
        f"  \u2502  PASS  {password}\n"
        f"  \u2502  TIME  {_now()}\n"
        "  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518\n\n"
        "\u2699\ufe0f  STEP-BY-STEP GUIDE\n"
        "  \u2192  Press Win+R  \u2192  type mstsc  \u2192  hit Enter\n"
        f"  \u2192  Computer:  {ip}:{port}\n"
        f"  \u2192  Username:  {username}\n"
        f"  \u2192  Password:  {password}\n\n"
        "\U0001f680  No registration. No payment. Ever.\n\n"
        f"\U0001f4e3  {CHANNEL_TAG}  \u00b7  {CHANNEL_LINK}"
    )


# ─────────────────────────────────────────────────────────────────────────
# Template 10: MATRIX
# ─────────────────────────────────────────────────────────────────────────
def _t_matrix(ip, port, username, password, country_name, country_flag):
    shade = "\u2591" * 18
    return (
        "\U0001f4bb  MATRIX ENTRY \u2014 FREE SERVER ACCESS\n"
        f"{shade}\n\n"
        "[ SYSTEM BREACH DETECTED ]\n"
        f"[ TARGET: {country_flag} {country_name}  \u00b7  PORT {port} ]\n"
        f"[ STATUS: \U0001f7e2 ONLINE  \u00b7  ACCESS GRANTED ]\n\n"
        f"  \u25b6  IP       {ip}\n"
        f"  \u25b6  PORT     {port}\n"
        f"  \u25b6  USER     {username}\n"
        f"  \u25b6  PASS     {password}\n"
        f"  \u25b6  TIME     {_now()}\n"
        "  \u25b6  OS       Windows Server \u00b7 Full Admin\n\n"
        f"{shade}\n\n"
        f"\u2328\ufe0f  COMMAND: mstsc \u2192 {ip}:{port}\n"
        "\U0001f4f1  MOBILE:  Microsoft RD Client app\n\n"
        "\U0001f4be  Save this \u00b7 Share this \u00b7 Use it\n\n"
        f"\U0001f4e3  {CHANNEL_TAG}  \u00b7  {CHANNEL_LINK}"
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
