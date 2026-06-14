CONTENT_TEMPLATES = {
    "educational": {
        "prompt": """Create an educational post about "{topic}" for a premium VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
🧠 [CATCHY TITLE IN CAPS]

━━━━━━━━━━━━━━━━━━━━━

[1–2 line hook that makes the reader need to keep reading]

📌 [Section heading]
[Content — 2–3 short lines]

📌 [Section heading]
[Content — 2–3 short lines]

📌 [Section heading]
[Content — 2–3 short lines]

━━━━━━━━━━━━━━━━━━━━━
💡 Pro Tip: [one punchy actionable tip]

🚀 [Call to action line]
```

Rules:
- Emoji dividers (━━━) between sections create premium look — always use them
- Each section starts with 📌 or a relevant emoji (🔒 for security, ⚡ for speed, 💰 for cost)
- Short punchy sentences — max 2 lines per section
- End with a strong CTA
- Length: 200–320 words
- Topic: {topic}""",
    },

    "marketing": {
        "prompt": """Create a marketing post about "{topic}" for a premium VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
🔥 [BOLD CLAIM OR OFFER — ALL CAPS]

[Pain point or question — 1 line that hits hard]

✅  [Benefit 1 — short and punchy]
✅  [Benefit 2 — short and punchy]
✅  [Benefit 3 — short and punchy]
✅  [Benefit 4 — short and punchy]

─────────────────────
⚡ [Specific stat or proof point]
─────────────────────

[1–2 lines of social proof or urgency]

👉 [Strong single CTA]
```

Rules:
- Opening line must create immediate desire or FOMO
- Each ✅ benefit must have a specific number or concrete detail (not vague)
- The separator line ─────── makes it look premium
- ⚡ stat must feel credible (uptime %, response time, price)
- Length: 150–220 words
- Topic: {topic}""",
    },

    "technical": {
        "prompt": """Create a technical tutorial post about "{topic}" for developers and sysadmins on Telegram.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
⚙️ [TECHNICAL TITLE — specific and clear]

━━━━━━━━━━━━━━━━━━━━━
🎯 The Problem
[1–2 lines: what pain does this solve?]

━━━━━━━━━━━━━━━━━━━━━
🛠 The Fix

Step 1 → [action]
`command or code here`

Step 2 → [action]
`command or code here`

Step 3 → [action]
`command or code here`

━━━━━━━━━━━━━━━━━━━━━
⚠️ Common Mistake: [what to avoid]
💡 Pro Tip: [extra value]

🔖 Save this post — you'll need it.
```

Rules:
- Use → arrows for step flow (looks clean in Telegram)
- Always include real commands in backtick code blocks
- ⚠️ and 💡 lines add credibility and make it worth saving
- End with "Save this post" — triggers the save behavior
- Length: 300–450 words
- Topic: {topic}""",
    },

    "announcement": {
        "prompt": """Create a company announcement about "{topic}" for a VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
📣 ANNOUNCEMENT

━━━━━━━━━━━━━━━━━━━━━

[ONE bold sentence stating the news — make it undeniable]

━━━━━━━━━━━━━━━━━━━━━

🗓  What's changing: [1–2 lines]
👥  Who it affects: [1 line]
⏱  When: [specific timeframe]
🎁  What you get: [the benefit for the customer]

━━━━━━━━━━━━━━━━━━━━━
👇 [Single clear action or next step]
```

Rules:
- The top box (━━━) framing creates visual authority
- Each detail line starts with a relevant emoji + label
- Tone: clear, direct, no fluff
- Length: 100–180 words
- Topic: {topic}""",
    },

    "comparison": {
        "prompt": """Create a comparison post about "{topic}" for a VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
⚖️ [OPTION A] vs [OPTION B]
━━━━━━━━━━━━━━━━━━━━━

[1 line hook — why this comparison matters]

━━━━━━━━━━━━━━━━━━━━━
🔵 [OPTION A]
➕ [Strength 1]
➕ [Strength 2]
➖ [Weakness]
💰 Price range: [...]

🔴 [OPTION B]
➕ [Strength 1]
➕ [Strength 2]
➖ [Weakness]
💰 Price range: [...]

━━━━━━━━━━━━━━━━━━━━━
🏆 Verdict:
[2–3 lines: who should pick which and why]

💬 Which do YOU use? Comment below 👇
```

Rules:
- Color-coded sections (🔵 vs 🔴) make it instantly scannable
- ➕ and ➖ are cleaner than ✅/❌ for comparison
- Verdict must give a clear winner for specific use cases
- Length: 200–320 words
- Topic: {topic}""",
    },

    "promotion": {
        "prompt": """Create a limited-time promotional post about "{topic}" for a VPS/Cloud Hosting Telegram channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
🎯 LIMITED OFFER — [DISCOUNT OR DEAL IN CAPS]

⏳ [Time limit — e.g., "Ends in 48 hours" or "First 50 users only"]

━━━━━━━━━━━━━━━━━━━━━
📦 What you get:
   ▸ [Item 1 with specific spec]
   ▸ [Item 2 with specific spec]
   ▸ [Item 3 with specific spec]
   ▸ [Item 4 with specific spec]

💵 Price: ~~[Original]~~ → [Deal price]

━━━━━━━━━━━━━━━━━━━━━
🔥 [Urgency line — why act now]

👉 [Single CTA with link placeholder or action]
```

Rules:
- ~~strikethrough~~ original price creates visual contrast (works in Telegram)
- ▸ bullets look more premium than dashes
- ⏳ at the top creates immediate urgency before they even read the offer
- Length: 130–200 words
- Topic: {topic}""",
    },

    "viral_giveaway": {
        "prompt": """Write a FREE giveaway post for a Telegram VPS/server channel.

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
🚨🎁 FREE [THING] GIVEAWAY — [NUMBER] SPOTS LEFT 🎁🚨

[One-line hook that creates instant FOMO]

━━━━━━━━━━━━━━━━━━━━━
🏆 What you win:
   🔹 [Specific prize 1]
   🔹 [Specific prize 2]
   🔹 [Specific prize 3]

⚡ How to enter (takes 10 seconds):
   1️⃣  Join this channel
   2️⃣  Comment "IN" below
   3️⃣  That's it. Done.

━━━━━━━━━━━━━━━━━━━━━
⏳ Closes when [number] people comment
🎰 Winners picked randomly & announced here

WHY are we doing this? [1-line authentic reason]

🔔 Share with a friend who needs this 👇
```

Rules:
- 🔹 bullets inside the prize box look clean and premium
- 1️⃣2️⃣3️⃣ number emojis for steps feel official
- "WHY" line is critical — it makes the giveaway feel real not spammy
- End with share nudge
- Length: 120–170 words""",
    },

    "viral_poll_engagement": {
        "prompt": """Write a highly engaging POLL/QUESTION post for a Telegram VPS/server channel.

Topic hint: {topic}

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
🗳️ QUICK POLL — WE NEED YOUR ANSWER

[One punchy provocative question about servers/VPS/hosting]

━━━━━━━━━━━━━━━━━━━━━
Vote by replying:

🅰️  [Option A — specific, relatable]
🅱️  [Option B — specific, relatable]
🅾️  [Option C — the unexpected one]
🆇  [Option D — "None / something else"]

━━━━━━━━━━━━━━━━━━━━━
💬 [Why you're asking — 1–2 lines. Makes it feel real.]

📊 We'll share the results + a FREE tip based on the top answer.

🔁 Forward to your sysadmin friends — the more votes, the better the data!
```

Rules:
- Letter emoji buttons (🅰️🅱️🅾️🆇) are unique and eye-catching
- The "free tip based on results" promise drives votes
- Forward nudge at the end is organic growth
- Length: 80–130 words""",
    },

    "viral_tip_secret": {
        "prompt": """Write a "secret tip / hidden trick" post about VPS, servers, or hosting.

Topic: {topic}

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
🤫 MOST SYSADMINS DON'T KNOW THIS...

[Bold hook — the promise of the secret. 1 line.]

━━━━━━━━━━━━━━━━━━━━━
🔍 The Problem Nobody Talks About:
[2–3 lines describing the pain point]

━━━━━━━━━━━━━━━━━━━━━
💡 The Secret Fix:
[Clear explanation — be specific]

```bash
[actual command or code]
```

━━━━━━━━━━━━━━━━━━━━━
📈 Result: [specific benefit — time saved / money saved / % improvement]

🔖 SAVE this. You'll thank yourself later.
↩️  Forward to anyone running a server.
```

Rules:
- The "problem nobody talks about" framing hooks curiosity
- MUST include a real command or concrete example — vague tips get ignored
- "SAVE this" + "Forward" double CTA at end maximizes reach
- Length: 150–220 words""",
    },

    "viral_free_resource": {
        "prompt": """Write a post offering a FREE valuable resource related to VPS/servers/Linux.

Topic hint: {topic}

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
📦 FREE [RESOURCE TYPE] DROP
━━━━━━━━━━━━━━━━━━━━━

[1-line hook: the ONE thing that makes this unmissable]

━━━━━━━━━━━━━━━━━━━━━
✅ What's inside:

   ✦ [Item 1 — specific, not vague]
   ✦ [Item 2 — specific, not vague]
   ✦ [Item 3 — specific, not vague]
   ✦ [Item 4 — specific, not vague]
   ✦ [Item 5 — specific, not vague]

━━━━━━━━━━━━━━━━━━━━━
🙋 Perfect for: [who needs this — 1 line]
⚡ Saves you: [time/money/effort — be specific]

━━━━━━━━━━━━━━━━━━━━━
💬 Reply "SEND" and I'll DM it to you.
📢 Share with your team — this one's too good to keep.
```

Rules:
- ✦ star bullets look unique and premium (different from boring checkmarks)
- "SEND" reply CTA is the best engagement driver on Telegram
- "Too good to keep" share nudge is subtle but effective
- Length: 140–210 words""",
    },

    "viral_news_hook": {
        "prompt": """Write a BREAKING NEWS or TREND post about the VPS/cloud/tech world.

Topic: {topic}

LANGUAGE RULE: Write ENTIRELY in English. No Persian, Arabic, or non-Latin characters.

FORMATTING — follow this exact visual style:

```
🚨 BREAKING — [HEADLINE IN CAPS]

[subheadline — 1 line adding detail or context]

━━━━━━━━━━━━━━━━━━━━━
📰 What happened:
[2–3 lines. Facts only. Clear and direct.]

━━━━━━━━━━━━━━━━━━━━━
💥 Why it matters to YOU:
[2–3 lines. Practical impact for VPS/server users.]

━━━━━━━━━━━━━━━━━━━━━
🧠 Our take:
[2–3 lines of expert opinion — confident, direct voice]

━━━━━━━━━━━━━━━━━━━━━
💬 What do you think? Drop your reaction below 👇
🔔 Share this with your network — they need to know.
```

Rules:
- 4-section structure (What / Why it matters / Our take / CTA) = authority format
- "Our take" positions the channel as an expert voice, not just a news aggregator
- Share nudge and comment CTA both at end for max engagement
- Length: 130–190 words""",
    },
}


def get_content_prompt(content_type: str, topic: str, language: str) -> str:
    template = CONTENT_TEMPLATES.get(content_type, CONTENT_TEMPLATES["educational"])
    return template["prompt"].format(topic=topic, language=language)


def get_all_content_types() -> list[str]:
    return list(CONTENT_TEMPLATES.keys())


def get_viral_content_types() -> list[str]:
    return ["viral_giveaway", "viral_poll_engagement", "viral_tip_secret", "viral_free_resource", "viral_news_hook"]
