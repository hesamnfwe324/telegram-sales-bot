CONTENT_TEMPLATES = {
    "educational": {
        "prompt": """Create an educational post about "{topic}" for a premium VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
🧠 [CATCHY TITLE IN CAPS — make it unmissable]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1–2 line hook — the single most important insight a reader gets from this]

📌 [Section heading]
[Content — 2–3 short, punchy lines]

📌 [Section heading]
[Content — 2–3 short, punchy lines]

📌 [Section heading]
[Content — 2–3 short, punchy lines]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 Pro Tip: [one concrete, actionable tip that adds real value]

🚀 [Strong CTA — drive engagement or channel growth]

🔖 Save this — you'll thank yourself later.
```

Rules:
- Emoji dividers (━━━) between sections create premium look — always use them
- Each section starts with 📌 or a relevant emoji (🔒 security, ⚡ speed, 💰 cost, 🛡️ protection)
- Short punchy sentences — max 2 lines per section
- Save this post trigger at the end boosts channel saves
- Length: 220–340 words
- Topic: {topic}
- Style: {style_hint}
- Unique angle seed: {unique_seed}
- Avoid these angles (already used): {forbidden_angles}""",
    },

    "marketing": {
        "prompt": """Create a high-converting marketing post about "{topic}" for a premium VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
🔥 [BOLD VALUE CLAIM — ALL CAPS, no fluff]

[Pain point question — 1 devastating line that hits hard]

✅  [Benefit 1 — specific number or concrete detail]
✅  [Benefit 2 — specific number or concrete detail]
✅  [Benefit 3 — specific number or concrete detail]
✅  [Benefit 4 — specific number or concrete detail]
✅  [Benefit 5 — specific number or concrete detail]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ [Credible stat or proof point — uptime %, speed, price, response time]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1–2 lines of urgency or social proof]

👉 [Single strong CTA — make it irresistible]
📲 Share this with someone who needs a reliable server.
```

Rules:
- Opening line must create immediate desire or FOMO
- Each ✅ benefit must have a specific number or concrete detail
- ⚡ stat must feel credible and impressive
- Length: 160–240 words
- Topic: {topic}
- Style: {style_hint}
- Unique angle seed: {unique_seed}
- Avoid these angles (already used): {forbidden_angles}""",
    },

    "technical": {
        "prompt": """Create a technical step-by-step tutorial post about "{topic}" for developers and sysadmins on Telegram.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
⚙️ [TECHNICAL TITLE — specific, clear, results-focused]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 The Problem
[1–2 lines: what pain or challenge does this solve?]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛠 The Solution

Step 1 → [clear action label]
`command or code here`

Step 2 → [clear action label]
`command or code here`

Step 3 → [clear action label]
`command or code here`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ Common Mistake: [what most people get wrong]
💡 Pro Tip: [the insider knowledge that changes everything]

📌 Expected Result: [what success looks like in 1 line]

🔖 Save this — it's the guide you'll reopen at 2am.
```

Rules:
- → arrows for step flow (clean in Telegram)
- Real commands in backtick code blocks — no fake commands
- ⚠️ and 💡 lines add credibility and make it worth saving
- Save trigger at the end drives bookmarks
- Length: 300–450 words
- Topic: {topic}
- Style: {style_hint}
- Unique angle seed: {unique_seed}
- Avoid these angles (already used): {forbidden_angles}""",
    },

    "announcement": {
        "prompt": """Create a company announcement post about "{topic}" for a VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
📣 OFFICIAL ANNOUNCEMENT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[ONE bold sentence stating the news — make it undeniable and exciting]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🗓  What's new: [1–2 lines]
👥  Who benefits: [1 line]
⏱  When: [specific timeframe]
🎁  What you get: [the tangible benefit for the customer]
🔗  How to access: [direct link or action step]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👇 [Single clear next step — tap, click, or share]
📲 Forward this to a friend who needs this.
```

Rules:
- Top frame (━━━) creates visual authority
- Each line starts with a relevant emoji + label
- Tone: direct, exciting, zero fluff
- Length: 120–200 words
- Topic: {topic}
- Style: {style_hint}
- Unique angle seed: {unique_seed}
- Avoid these angles (already used): {forbidden_angles}""",
    },

    "comparison": {
        "prompt": """Create a comparison post about "{topic}" for a VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
⚖️ [OPTION A] vs [OPTION B] — THE REAL DIFFERENCE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1 line hook — why this comparison matters to your server decision]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔵 [OPTION A]
✅ [Advantage 1]
✅ [Advantage 2]
❌ [Main weakness]

🔴 [OPTION B]
✅ [Advantage 1]
✅ [Advantage 2]
❌ [Main weakness]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 Winner for most users: [OPTION X]
Why: [1–2 concrete reason lines]

💬 Which one do YOU use? Drop your answer below.
🔖 Save this — share it before the next server debate.
```

Rules:
- Always declare a winner — fence-sitting loses readers
- 💬 engagement line triggers comments
- Length: 200–300 words
- Topic: {topic}
- Style: {style_hint}
- Unique angle seed: {unique_seed}
- Avoid these angles (already used): {forbidden_angles}""",
    },

    "promotion": {
        "prompt": """Create a promotional offer post about "{topic}" for a VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
🎁 LIMITED TIME OFFER — DON'T SCROLL PAST THIS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1–2 lines: the deal in plain language — price, what you get, why now]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 What's included:
✅ [Feature 1 — with spec or value]
✅ [Feature 2 — with spec or value]
✅ [Feature 3 — with spec or value]
✅ [Feature 4 — with spec or value]

⏳ Offer expires: [timeframe — create urgency]
💰 Price: [price point — anchor with original price if discounted]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 [Strong single CTA — claim now / get yours / activate deal]
📲 Tag a friend who needs a server upgrade.
```

Rules:
- Open with urgency — the deal must feel like it expires
- Each ✅ feature must have a concrete spec or value
- Anchor pricing psychology — show what they save
- Length: 150–220 words
- Topic: {topic}
- Style: {style_hint}
- Unique angle seed: {unique_seed}
- Avoid these angles (already used): {forbidden_angles}""",
    },

    "viral_giveaway": {
        "prompt": """Create a viral giveaway post about "{topic}" for a VPS/Cloud Hosting Telegram channel to maximize new member joins.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact viral style:

```
🎉 FREE [PRIZE] GIVEAWAY — ENDING SOON

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1 line — the most exciting thing about this prize]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 What you win:
✅ [Prize detail 1 — specific and valuable]
✅ [Prize detail 2 — specific and valuable]
✅ [Prize detail 3 — specific and valuable]

🔑 How to enter (takes 30 seconds):
1️⃣ Join this channel
2️⃣ Forward this post to 1 friend
3️⃣ Drop a ✅ in the comments

⏳ Winners announced: [timeframe]
👥 [Number] winners selected randomly

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 Don't miss this — share now before it ends!
```

Rules:
- Prize must feel genuinely valuable (VPS, RDP, server time, bandwidth)
- Entry steps drive sharing = channel growth
- Length: 150–220 words
- Topic: {topic}
- Style: {style_hint}
- Unique angle seed: {unique_seed}
- Avoid these angles (already used): {forbidden_angles}""",
    },

    "viral_free_resource": {
        "prompt": """Create a viral free resource post about "{topic}" for a VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact viral style:

```
🆓 FREE [RESOURCE NAME] — SAVE THIS NOW

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1 line — the specific value someone gets in 60 seconds]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 What's inside:
✅ [Resource item 1 — specific and actionable]
✅ [Resource item 2 — specific and actionable]
✅ [Resource item 3 — specific and actionable]
✅ [Resource item 4 — specific and actionable]
✅ [Resource item 5 — specific and actionable]

💡 Why this matters:
[2–3 lines: the problem this solves + who it's for]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📥 How to get it: [1-step clear instruction]
🔖 Save this post — share it with your team.
```

Rules:
- Resource must feel like a real, high-value cheat sheet or guide
- "Save this now" drives bookmarks — use it
- Length: 180–260 words
- Topic: {topic}
- Style: {style_hint}
- Unique angle seed: {unique_seed}
- Avoid these angles (already used): {forbidden_angles}""",
    },

    "viral_tip_secret": {
        "prompt": """Create a viral insider tip/secret post about "{topic}" for a VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact viral style:

```
🤫 [NUMBER] SERVER SECRETS MOST ADMINS DON'T KNOW

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1 shocking hook — the insight that makes people stop scrolling]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 Secret #1: [Name]
[2–3 lines of real insider insight]

🔍 Secret #2: [Name]
[2–3 lines of real insider insight]

🔍 Secret #3: [Name]
[2–3 lines of real insider insight]

🔍 Secret #4: [Name]
[2–3 lines of real insider insight]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 Which one surprised you most? Reply below.
🔖 Save this — and share it with your server team.
```

Rules:
- Secrets must be genuinely non-obvious — not beginner basics
- 💬 engagement line drives comments
- Length: 250–380 words
- Topic: {topic}
- Style: {style_hint}
- Unique angle seed: {unique_seed}
- Avoid these angles (already used): {forbidden_angles}""",
    },

    "viral_poll_engagement": {
        "prompt": """Create a viral poll/engagement post about "{topic}" for a VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact viral style:

```
📊 QUICK POLL — VOTE NOW

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1 polarizing question about {topic} — something every sysadmin has an opinion on]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🅰️ [Option A — specific and opinionated]
🅱️ [Option B — specific and opinionated]
🅲 [Option C — the wildcard answer]
🅳 [Option D — the "it depends" answer done interestingly]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 Drop your letter in the comments + tell us WHY.
📊 Results posted when we hit [number] votes!

[1–2 lines of educational context that makes voting more interesting]
🔗 Share this with your team and see who disagrees.
```

Rules:
- Question must be genuinely polarizing — not obvious
- Options must be distinct and interesting
- Comments driver is required
- Length: 150–220 words
- Topic: {topic}
- Style: {style_hint}
- Unique angle seed: {unique_seed}
- Avoid these angles (already used): {forbidden_angles}""",
    },

    "viral_news_hook": {
        "prompt": """Create a viral news-hook post about "{topic}" for a VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact viral style:

```
🚨 [BIG NEWS OR TREND] — What This Means For YOUR Server

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1–2 lines: the news or trend + why it matters RIGHT NOW]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 What happened:
[2–3 lines of clear context]

⚠️ What it means for you:
[2–3 lines of direct practical impact]

✅ What to do now:
[3–4 concrete action steps with → arrows]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 Does this affect your setup? Comment below.
🔖 Save this + share before everyone else finds out.
```

Rules:
- Open with urgency — this is breaking or trending
- Action steps are concrete and immediately doable
- Length: 220–320 words
- Topic: {topic}
- Style: {style_hint}
- Unique angle seed: {unique_seed}
- Avoid these angles (already used): {forbidden_angles}""",
    },
}


def get_content_prompt(
    content_type: str,
    topic: str,
    language: str = "en",
    style_hint: str = "",
    forbidden_angles: list[str] | None = None,
    unique_seed: int | None = None,
) -> str:
    template = CONTENT_TEMPLATES.get(content_type, CONTENT_TEMPLATES["educational"])
    prompt = template["prompt"].format(
        topic=topic,
        language=language,
        style_hint=style_hint or "default",
        forbidden_angles=", ".join(forbidden_angles or []) or "none",
        unique_seed=unique_seed or 0,
    )
    return prompt


def get_all_content_types() -> list[str]:
    return list(CONTENT_TEMPLATES.keys())
