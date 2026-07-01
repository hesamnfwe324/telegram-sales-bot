"""
RDP Post Builder — single fixed template (THUNDER DROP).
Username is always hardcoded as Administrator.
Images are always RDP / VPS / Server / VDS themed.
"""
import urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")
FIXED_USERNAME = "Administrator"
_URL_SEPARATOR = "|||"

_RDP_IMAGE_PROMPTS = [
    "Windows Remote Desktop connection screen, RDP login interface, blue professional theme, server credentials panel, ultra HD photorealistic",
    "RDP remote desktop session active, Windows Server taskbar, multiple monitor setup, dark IT workspace, cinematic lighting",
    "Windows Server 2022 datacenter edition interface, administrator dashboard, server manager open, dark dramatic lighting",
    "Remote desktop protocol visualization, encrypted connection tunnel, Windows server access, glowing blue neon, cyberpunk tech art",
    "Virtual Private Server VPS hosting panel, resource usage graphs, CPU RAM disk stats, dark dashboard UI, professional",
    "VPS cloud server infrastructure, floating virtual machine containers, isolated nodes glowing blue, dark background, 3D render",
    "VPS server farm visualization, rows of virtual machines, cloud hosting platform, neon blue purple lighting, cinematic",
    "Premium VPS hosting environment, server control panel dashboard, uptime metrics, dark sleek UI, ultra HD",
    "Dedicated server rack hardware, blade servers glowing LEDs, enterprise datacenter room, dramatic dark lighting, photorealistic 8K",
    "Server room interior, rows of rack servers, blinking status lights, blue orange neon glow, cinematic wide angle",
    "Professional datacenter servers, ceiling-mounted cooling, cable management, dramatic lighting, ultra realistic photography",
    "Enterprise server hardware closeup, CPU heatsinks RAM sticks, glowing circuits, dark tech aesthetic, macro 8K",
    "Virtual Dedicated Server VDS cloud platform, virtual machine isolation, dedicated resources visualization, dark background neon",
    "VDS server management dashboard, dedicated virtual instance, resource allocation panel, sleek dark UI, professional",
    "VDS infrastructure diagram, dedicated virtual nodes, network topology, glowing connections, dark futuristic 3D art",
]

_IMAGE_STYLES = [
    "ultra-realistic 8K professional photography, cinematic lighting, dark tech aesthetic",
    "futuristic 3D render, glowing neon blue circuits, hyper-detailed, dark background, dramatic",
    "photorealistic datacenter photography, professional HDR, dramatic shadows and highlights",
]


def _pollinations_url(prompt: str, seed: int) -> str:
    encoded = urllib.parse.quote(prompt)
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1280&height=720&model=flux&seed={seed}&nologo=true&enhance=true"
    )


def _generate_image_urls(seed: int) -> str:
    prompt = _RDP_IMAGE_PROMPTS[seed % len(_RDP_IMAGE_PROMPTS)]
    urls = []
    for i, style in enumerate(_IMAGE_STYLES):
        full_prompt = f"{prompt}, {style}"
        urls.append(_pollinations_url(full_prompt, seed + i * 7919))
    return _URL_SEPARATOR.join(urls)


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

    image_urls = _generate_image_urls(seed)
    return text, image_urls
