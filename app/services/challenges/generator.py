import json
import re
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _fallback_content(topic: str, language: str) -> dict[str, Any]:
    if language == "fa":
        return {
            "title": f"چالش RDP: {topic}",
            "question": f"کدام گزینه برای اتصال امن‌تر به یک سرور RDP توصیه می‌شود؟ موضوع: {topic}",
            "answers": [
                "فعال‌سازی احراز هویت چندمرحله‌ای و محدودکردن دسترسی",
                "انتشار رمز عبور در یک کانال عمومی",
                "استفاده از رمز عبور کوتاه و تکراری",
                "بازگذاشتن پورت RDP برای همه اینترنت",
            ],
            "correct_answer": 0,
            "reward": settings.CHALLENGE_DEFAULT_REWARD,
            "hashtags": ["#چالش", "#RDP", "#سرور", "#امنیت_سایبری"],
            "seo_keywords": ["RDP", "سرور مجازی", "امنیت سرور", "Remote Desktop"],
        }
    return {
        "title": f"RDP Challenge: {topic}",
        "question": f"Which practice is safer for an RDP server? Topic: {topic}",
        "answers": [
            "Enable MFA and restrict access",
            "Post the password publicly",
            "Reuse a short password",
            "Leave RDP open to everyone",
        ],
        "correct_answer": 0,
        "reward": settings.CHALLENGE_DEFAULT_REWARD,
        "hashtags": ["#Challenge", "#RDP", "#Server", "#CyberSecurity"],
        "seo_keywords": ["RDP", "VPS", "server security", "Remote Desktop"],
    }


def _clean_json(text: str) -> dict[str, Any]:
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    payload = fenced.group(1) if fenced else text.strip()
    return json.loads(payload)


def _validate_content(content: dict[str, Any], topic: str, language: str) -> dict[str, Any]:
    required = ("title", "question", "answers", "correct_answer", "reward", "hashtags", "seo_keywords")
    if any(key not in content for key in required):
        raise ValueError("Grok response is missing required challenge fields")
    answers = content["answers"]
    correct_answer = content["correct_answer"]
    if not isinstance(answers, list) or len(answers) != 4:
        raise ValueError("A challenge must have exactly four answers")
    if not isinstance(correct_answer, int) or correct_answer not in range(4):
        raise ValueError("correct_answer must be an answer index from 0 to 3")
    content["title"] = str(content["title"])[:500]
    content["question"] = str(content["question"])[:4000]
    content["answers"] = [str(answer)[:500] for answer in answers]
    content["reward"] = str(content["reward"])[:500]
    content["hashtags"] = [str(tag)[:80] for tag in content["hashtags"][:12]]
    content["seo_keywords"] = [str(keyword)[:120] for keyword in content["seo_keywords"][:12]]
    return content


async def generate_challenge_content(topic: str, language: str = "fa") -> dict[str, Any]:
    """Generate a safe, educational engagement challenge with Grok."""
    if not settings.XAI_API_KEY:
        logger.warning("xai_key_not_configured_using_safe_fallback")
        return _fallback_content(topic, language)

    client = AsyncOpenAI(
        api_key=settings.XAI_API_KEY,
        base_url=settings.XAI_BASE_URL,
        timeout=60.0,
        max_retries=1,
    )
    system = (
        "You create ethical Telegram engagement challenges for an RDP and VPS community. "
        "Return JSON only. Never request passwords, tokens, personal data, spam, fake activity, "
        "or unsafe access instructions. Keep the challenge educational and suitable for a public channel. "
        "Use the requested language."
    )
    prompt = f"""
Create one exciting but truthful multiple-choice challenge about RDP, VPS, remote desktop,
server reliability, or cybersecurity.
Language: {language}
Topic: {topic}
Return exactly this JSON shape:
{{
  "title": "short title",
  "question": "one clear question",
  "answers": ["answer 1", "answer 2", "answer 3", "answer 4"],
  "correct_answer": 0,
  "reward": "a transparent non-guaranteed reward description",
  "hashtags": ["#RDP", "#..."],
  "seo_keywords": ["RDP", "VPS", "هشتگ یا کلیدواژه مرتبط"]
}}
The correct_answer is a zero-based index. Make all four choices plausible.
"""
    try:
        response = await client.chat.completions.create(
            model=settings.XAI_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=1200,
            response_format={"type": "json_object"},
        )
        content = _clean_json(response.choices[0].message.content or "")
        return _validate_content(content, topic, language)
    except Exception as exc:
        logger.error("xai_challenge_generation_failed_using_fallback", error=str(exc))
        return _fallback_content(topic, language)