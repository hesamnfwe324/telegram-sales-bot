"""
    RDP Post Builder — 10 unique templates for free RDP/VPS/SERVER posts.
    Template is chosen by seed so consecutive posts never look the same.
    Images generated via Pollinations.ai (free, no API key required).
    """
    import random
    import urllib.parse
    from datetime import datetime
    from zoneinfo import ZoneInfo

    TEHRAN = ZoneInfo("Asia/Tehran")

    CHANNEL_TAG  = "@VPS24H"
    CHANNEL_LINK = "t.me/VPS24H"

    ADMIN_SIGNATURES = [
      "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👑  Official Admin  |  @VPS24H",
      "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\u269c\ufe0f  Verified Admin  \u00b7  @VPS24H",
      "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\U0001f531  Director & Admin  \u203a  @VPS24H",
      "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\U0001f6e1\ufe0f  Head of Operations  \u203a  @VPS24H",
      "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔐  Certified Admin  \u203a  @VPS24H",
      "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💎  Senior Admin  |  @VPS24H",
      "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🌍  Network Admin  \u00b7  @VPS24H",
      "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚡  Chief Admin  |  @VPS24H",
      "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🚀  Channel Lead  \u203a  @VPS24H",
      "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🏆  Authorized Admin  \u00b7  @VPS24H",
    ]

    HASHTAG_POOLS = [
      "#FreeRDP #FreeVPS #FreeServer #RDP #VPS #Windows #Server #FreeAccess #VPS24H",
      "#RDPFree #VPSFree #ServerFree #WindowsServer #RemoteDesktop #CloudServer #FreeRDP",
      "#FreeRDPServer #WindowsRDP #ServerAccess #FreeCloud #VPS24H #FreeVPS #RDP2025",
      "#RemoteAccess #ServerGiveaway #FreeServer #RDP #VPS #Windows #FreeAccess #VPS24H",
      "#FreeVPS2025 #FreeRDP2025 #WindowsServer #RemoteDesktop #ServerDrop #VPS24H",
    ]

    RDP_IMAGE_PROMPTS = [
      "Windows Remote Desktop connection professional interface data center server room blue white tech 8K ultra realistic",
      "Futuristic VPS server room glowing blue racks network cables computing infrastructure dark dramatic cinematic lighting",
      "Windows Server 2022 dashboard remote desktop connection screen cybersecurity digital technology professional",
      "Premium cloud server datacenter rows servers orange glowing lights professional high-tech environment dramatic",
      "Free RDP access concept computer monitor remote desktop unlock key digital freedom technology neon colors dark",
      "Server room blinking LED lights ethernet cables modern datacenter infrastructure cinematic professional photography",
      "Abstract digital server network RDP connection tunnel encrypted data transfer neon blue dark background",
      "Windows Server system administrator multiple screens corporate tech environment professional clean workspace",
      "Cloud computing infrastructure virtual private server floating servers icons blue technology futuristic background",
      "Cyberpunk datacenter aesthetic neon-lit server racks futuristic computing ultra-detailed dark tech art",
      "Professional remote desktop connection corporate server access secure login interface clean corporate design",
      "High-performance VPS server stack multiple virtual machines cloud hosting concept modern technology art render",
      "Digital fortress server security RDP protected connection lock over server rack cinematic dramatic lighting",
      "Aerial view massive datacenter premium hosting infrastructure cloud servers professional wide angle photography",
      "Free server giveaway concept gift box floating server icon cloud computing bright promotional design",
    ]

    FALLBACK_STYLES = [
      "ultra-realistic 8K professional photography, cinematic lighting, dark tech aesthetic",
      "futuristic 3D render, glowing neon circuits, hyper-detailed, dark background, dramatic lighting",
      "clean corporate illustration, vibrant gradient colors, modern professional design, sharp",
    ]

    _URL_SEPARATOR = "|||"


    def _pollinations_url(prompt: str, seed: int) -> str:
      encoded = urllib.parse.quote(prompt)
      return (
          f"https://image.pollinations.ai/prompt/{encoded}"
          f"?width=1280&height=720&model=flux&seed={seed}&nologo=true&enhance=true"
      )


    def generate_rdp_image_urls(seed: int) -> str:
      """3 unique RDP-themed image URLs with different seeds and visual styles."""
      base_prompt = RDP_IMAGE_PROMPTS[seed % len(RDP_IMAGE_PROMPTS)]
      urls = []
      for i, style in enumerate(FALLBACK_STYLES):
          s = seed + (i * 7919) + (i * 31)
          full_prompt = f"{base_prompt}, {style}"
          urls.append(_pollinations_url(full_prompt, s))
      return _URL_SEPARATOR.join(urls)


    # ─── Template builders ────────────────────────────────────────────────────────

    def _t_gift(ip, port, username, password, country_name, country_flag) -> str:
      return (
          f"🎁 FREE SERVER JUST DROPPED \u2014 {country_flag} {country_name}\n\n"
          f"Our scanner hunted this one down. It's yours. No strings attached.\n\n"
          f"\u2554{'\u2550' * 30}\u2557\n"
          f"\u2551   🖥️  FREE RDP ACCESS CARD   \u2551\n"
          f"\u255a{'\u2550' * 30}\u255d\n\n"
          f"🌍  Location    \u203a  {{country_flag}} {{country_name}}\n"
          f"🔗  IP Address  \u203a  {{ip}}\n"
          f"🔌  Port        \u203a  {{port}}\n"
          f"👤  Username    \u203a  {{username}}\n"
          f"🔑  Password    \u203a  {{password}}\n"
          f"💻  Type        \u203a  Windows RDP\n\n"
          f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
          f"⚡ Scanned & verified. Port open. Ready to connect.\n"
          f"⚠️  First come, first served. Don't sleep on this.\n\n"
          f"📣 {{CHANNEL_TAG}}  \u2022  {{CHANNEL_LINK}}"
      ).format(country_flag=country_flag, country_name=country_name,
               ip=ip, port=port, username=username, password=password,
               CHANNEL_TAG=CHANNEL_TAG, CHANNEL_LINK=CHANNEL_LINK)


    def _t_vip(ip, port, username, password, country_name, country_flag) -> str:
      return (
          f"💎 VIP SERVER UNLOCKED\n\n"
          f"{country_flag} A premium {{country_name}} RDP just appeared on our radar.\n"
          f"Grabbed it. Tested it. Giving it away. Free. No catch.\n\n"
          f"\u2580" * 29 + "\n"
          f"📌  SERVER CREDENTIALS\n"
          f"\u2584" * 29 + "\n\n"
          f"🌍  Country   \u2192  {{country_flag}} {{country_name}}\n"
          f"📡  Server    \u2192  {{ip}}:{{port}}\n"
          f"👤  User      \u2192  {{username}}\n"
          f"🔐  Pass      \u2192  {{password}}\n"
          f"🖥️   OS        \u2192  Windows Server\n\n"
          f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
          f"🏆 Free VPS  \u2022  Free RDP  \u2022  Free Server\n"
          f"⚡ Zero Cost. Full Access. Right Now.\n\n"
          f"📣 {{CHANNEL_TAG}}  \u2022  {{CHANNEL_LINK}}"
      ).format(country_flag=country_flag, country_name=country_name,
               ip=ip, port=port, username=username, password=password,
               CHANNEL_TAG=CHANNEL_TAG, CHANNEL_LINK=CHANNEL_LINK)


    def _t_secret(ip, port, username, password, country_name, country_flag) -> str:
      return (
          f"🔓 SECRET SERVER FOUND: {{country_flag}} {{country_name}}\n\n"
          f"Our scanners detected an exposed Windows server in {{country_name}}.\n"
          f"Normally costs $20+/month. You're getting it FREE today.\n\n"
          f"\u25c8{'\u2501' * 28}\u25c8\n"
          f"          🔑 ACCESS DETAILS\n"
          f"\u25c8{'\u2501' * 28}\u25c8\n\n"
          f"   IP       :  {{ip}}\n"
          f"   Port     :  {{port}}\n"
          f"   User     :  {{username}}\n"
          f"   Pass     :  {{password}}\n"
          f"   Country  :  {{country_flag}} {{country_name}}\n"
          f"   Type     :  Windows RDP Server\n\n"
          f"\u25c8{'\u2501' * 28}\u25c8\n"
          f"💡 Use it for bots, projects, automation \u2014 anything.\n"
          f"\u23f3 Limited window. Act fast.\n\n"
          f"📣 {{CHANNEL_TAG}}  \u2022  {{CHANNEL_LINK}}"
      ).format(country_flag=country_flag, country_name=country_name,
               ip=ip, port=port, username=username, password=password,
               CHANNEL_TAG=CHANNEL_TAG, CHANNEL_LINK=CHANNEL_LINK)


    def _t_cyber(ip, port, username, password, country_name, country_flag) -> str:
      now = datetime.now(TEHRAN).strftime("%Y-%m-%d %H:%M")
      return (
          f"⚡ CYBER DROP \u2014 FREE RDP SERVER\n\n"
          f"[ {{country_flag}} {{country_name}} | Port {{port}} | LIVE ]\n\n"
          f"Scanner locked on target. Full Windows access. Completely FREE.\n\n"
          f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
          f"🖥️  [SERVER]  {{ip}}:{{port}}\n"
          f"👤  [LOGIN]   {{username}}\n"
          f"🔑  [PASS]    {{password}}\n"
          f"🌍  [REGION]  {{country_flag}} {{country_name}}\n"
          f"\u23f1\ufe0f  [TIME]    {now}\n"
          f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
          f"🚀 Connect via Remote Desktop (mstsc) \u2192 Enter IP above\n"
          f"💡 Works on Windows, Mac, Android, iOS\n\n"
          f"📣 {{CHANNEL_TAG}}  \u2022  {{CHANNEL_LINK}}"
      ).format(country_flag=country_flag, country_name=country_name,
               ip=ip, port=port, username=username, password=password,
               CHANNEL_TAG=CHANNEL_TAG, CHANNEL_LINK=CHANNEL_LINK)


    def _t_alert(ip, port, username, password, country_name, country_flag) -> str:
      return (
          f"🚨 ALERT: FREE SERVER AVAILABLE \u2014 {{country_flag}} {{country_name}}\n\n"
          f"Our scanner picked up an open RDP in {{country_name}}.\n"
          f"Windows Server. Full access. No cost. Grab it now.\n\n"
          f"\u256d{'\u2500' * 29}\u256e\n"
          f"\u2502  \U0001f534 LIVE SERVER ALERT\n"
          f"\u251c{'\u2500' * 29}\u2524\n"
          f"\u2502  Country   {{country_flag}} {{country_name}}\n"
          f"\u2502  IP        {{ip}}\n"
          f"\u2502  Port      {{port}}\n"
          f"\u2502  Username  {{username}}\n"
          f"\u2502  Password  {{password}}\n"
          f"\u2502  Status    ✅ OPEN & READY\n"
          f"\u2570{'\u2500' * 29}\u256f\n\n"
          f"\u23f3 These windows don't stay open long.\n"
          f"🔥 Move fast. Connect. Enjoy.\n\n"
          f"📣 {{CHANNEL_TAG}}  \u2022  {{CHANNEL_LINK}}"
      ).format(country_flag=country_flag, country_name=country_name,
               ip=ip, port=port, username=username, password=password,
               CHANNEL_TAG=CHANNEL_TAG, CHANNEL_LINK=CHANNEL_LINK)


    def _t_hacker(ip, port, username, password, country_name, country_flag) -> str:
      return (
          f"💻 PORT SCANNER RESULT \u2014 FREE ACCESS INSIDE\n\n"
          f"{{country_flag}} Location: {{country_name}}\n"
          f"Method: Port Scanner | Port 3389 (RDP) | Result: OPEN\n\n"
          f"> Initializing connection...\n"
          f"> Credentials generated...\n"
          f"> Access: GRANTED ✅\n\n"
          f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
          f"  🔗  IP       {{ip}}\n"
          f"  🔌  PORT     {{port}}\n"
          f"  👤  USER     {{username}}\n"
          f"  🔑  PASS     {{password}}\n"
          f"  🌍  COUNTRY  {{country_flag}} {{country_name}}\n"
          f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
          f"System: Windows RDP  |  Cost: $0.00\n\n"
          f"📣 {{CHANNEL_TAG}}  \u2022  {{CHANNEL_LINK}}"
      ).format(country_flag=country_flag, country_name=country_name,
               ip=ip, port=port, username=username, password=password,
               CHANNEL_TAG=CHANNEL_TAG, CHANNEL_LINK=CHANNEL_LINK)


    def _t_luxury(ip, port, username, password, country_name, country_flag) -> str:
      return (
          f"👑 PREMIUM SERVER \u2014 COMPLIMENTARY ACCESS\n\n"
          f"Our network team sourced an exclusive {{country_flag}} {{country_name}} server\n"
          f"for our valued community. Yours at zero cost.\n\n"
          f"\u25c6\u25c7" * 10 + "\u25c6\n"
          f"   \u2726  EXCLUSIVE SERVER DETAILS  \u2726\n"
          f"\u25c6\u25c7" * 10 + "\u25c6\n\n"
          f"   🌍  Origin      {{country_flag}} {{country_name}}\n"
          f"   🔗  Host        {{ip}}\n"
          f"   🔌  Port        {{port}}\n"
          f"   👤  Identity    {{username}}\n"
          f"   🔐  Passphrase  {{password}}\n"
          f"   💻  Platform    Windows Server (RDP)\n\n"
          f"\u25c6\u25c7" * 10 + "\u25c6\n\n"
          f"💎 Complimentary. Premium. Limited availability.\n"
          f"🏆 Stay subscribed for daily server drops.\n\n"
          f"📣 {{CHANNEL_TAG}}  \u2022  {{CHANNEL_LINK}}"
      ).format(country_flag=country_flag, country_name=country_name,
               ip=ip, port=port, username=username, password=password,
               CHANNEL_TAG=CHANNEL_TAG, CHANNEL_LINK=CHANNEL_LINK)


    def _t_speed(ip, port, username, password, country_name, country_flag) -> str:
      return (
          f"⚡ LIGHTNING FAST FREE RDP \u2014 {{country_flag}} {{country_name}}\n\n"
          f"Scanner running at full speed. Found you a {{country_name}} RDP.\n"
          f"Low latency. High uptime. Zero dollars.\n\n"
          f"🔥{'\u2500' * 27}🔥\n"
          f"  SERVER   {{ip}}:{{port}}\n"
          f"  LOGIN    {{username}}\n"
          f"  PASS     {{password}}\n"
          f"  COUNTRY  {{country_flag}} {{country_name}}\n"
          f"  TYPE     Windows Remote Desktop\n"
          f"🔥{'\u2500' * 27}🔥\n\n"
          f"How to connect:\n"
          f"1\ufe0f\u20e3  Open Remote Desktop (mstsc)\n"
          f"2\ufe0f\u20e3  Enter: {{ip}}:{{port}}\n"
          f"3\ufe0f\u20e3  Login with credentials above\n"
          f"4\ufe0f\u20e3  You're in. Free. Just like that. \U0001f389\n\n"
          f"📣 {{CHANNEL_TAG}}  \u2022  {{CHANNEL_LINK}}"
      ).format(country_flag=country_flag, country_name=country_name,
               ip=ip, port=port, username=username, password=password,
               CHANNEL_TAG=CHANNEL_TAG, CHANNEL_LINK=CHANNEL_LINK)


    def _t_matrix(ip, port, username, password, country_name, country_flag) -> str:
      return (
          f"🟢 MATRIX BREACH \u2014 {{country_flag}} {{country_name}} SERVER\n\n"
          f"The system has been entered. Port 3389 confirmed open.\n"
          f"Credentials acquired. Transmitting to agents now.\n\n"
          f"[[ TARGET ACQUIRED ]]\n"
          f"════════════════════════════════\n"
          f"  LOCATION  ::  {{country_flag}} {{country_name}}\n"
          f"  ADDRESS   ::  {{ip}}\n"
          f"  PORT      ::  {{port}}\n"
          f"  OPERATOR  ::  {{username}}\n"
          f"  KEY       ::  {{password}}\n"
          f"  SYSTEM    ::  Windows RDP\n"
          f"  STATUS    ::  🟢 LIVE\n"
          f"════════════════════════════════\n"
          f"[[ END TRANSMISSION ]]\n\n"
          f"🚀 Enter the matrix. It's free.\n"
          f"💡 Use wisely. Share the access.\n\n"
          f"📣 {{CHANNEL_TAG}}  \u2022  {{CHANNEL_LINK}}"
      ).format(country_flag=country_flag, country_name=country_name,
               ip=ip, port=port, username=username, password=password,
               CHANNEL_TAG=CHANNEL_TAG, CHANNEL_LINK=CHANNEL_LINK)


    def _t_scanner_report(ip, port, username, password, country_name, country_flag) -> str:
      now = datetime.now(TEHRAN).strftime("%d %b %Y | %H:%M")
      return (
          f"📊 SCANNER REPORT \u2014 {{country_flag}} {{country_name}}\n\n"
          f"Date: {now}\n"
          f"Scan Type: RDP Port 3389 | {{country_name}} IP Range\n"
          f"Result: ✅ Open Port Detected\n\n"
          f"\u250c{'\u2500' * 30}\u2510\n"
          f"\u2502  🌍 SERVER DETAILS\n"
          f"\u2502  IP       {{ip}}\n"
          f"\u2502  Port     {{port}}\n"
          f"\u2502  User     {{username}}\n"
          f"\u2502  Pass     {{password}}\n"
          f"\u2502  OS       Windows Server\n"
          f"\u2502  Country  {{country_flag}} {{country_name}}\n"
          f"\u2502  Status   🟢 LIVE & FREE\n"
          f"\u2514{'\u2500' * 30}\u2518\n\n"
          f"🎁 Completely free. No registration required.\n"
          f"📌 Save this post. Use it anytime.\n\n"
          f"📣 {{CHANNEL_TAG}}  \u2022  {{CHANNEL_LINK}}"
      ).format(country_flag=country_flag, country_name=country_name,
               ip=ip, port=port, username=username, password=password,
               CHANNEL_TAG=CHANNEL_TAG, CHANNEL_LINK=CHANNEL_LINK)


    _TEMPLATES = [
      _t_gift,
      _t_vip,
      _t_secret,
      _t_cyber,
      _t_alert,
      _t_hacker,
      _t_luxury,
      _t_speed,
      _t_matrix,
      _t_scanner_report,
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
      Build an attractive RDP post text and image URLs.
      Template chosen by seed so consecutive posts never look the same.
      Returns (post_text, image_urls_string).
      """
      template_fn = _TEMPLATES[seed % len(_TEMPLATES)]
      body = template_fn(ip, port, username, password, country_name, country_flag)
      hashtags = random.choice(HASHTAG_POOLS)
      admin_sig = ADMIN_SIGNATURES[seed % len(ADMIN_SIGNATURES)]
      post_text = f"{body}\n\n{hashtags}{admin_sig}"
      image_urls = generate_rdp_image_urls(seed)
      return post_text, image_urls
    