from langdetect import detect, LangDetectException
from app.core.logging import get_logger
import hashlib
import unicodedata
from app.cache.redis_client import cache_get, cache_set

logger = get_logger(__name__)

SUPPORTED_LANGUAGES = {
    "en": "English",
    "fa": "Persian (Farsi)",
    "ar": "Arabic",
    "tr": "Turkish",
    "ru": "Russian",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
}

DEFAULT_LANGUAGE = "en"

# Persian-specific characters that don't exist in standard Arabic
_PERSIAN_EXCLUSIVE = set("پچژگکی‌")

# Arabic-specific characters that don't exist in Persian
# ث (theh), ذ (dhal), ظ (zah) — these letters are Arabic-only
_ARABIC_EXCLUSIVE = set("ثذظ")

def _detect_script(text: str) -> str | None:
    """
    Instantly detect language from Unicode script — works even for 1–4 char messages.
    Returns a language code or None if script is not conclusive.

    Persian vs Arabic disambiguation:
    - Has Persian-exclusive letters (پچژگ...) → fa
    - Has Arabic-exclusive letters (ثذظ)      → ar
    - Ambiguous (e.g. سلام shared by both)    → fa  (bot is Persian-first)
    """
    arabic_count = 0
    cyrillic_count = 0
    has_persian = False
    has_arabic_exclusive = False

    for ch in text:
        if ch in _PERSIAN_EXCLUSIVE:
            has_persian = True
        if ch in _ARABIC_EXCLUSIVE:
            has_arabic_exclusive = True
        cp = ord(ch)
        # Arabic/Persian Unicode block: U+0600–U+06FF
        if 0x0600 <= cp <= 0x06FF:
            arabic_count += 1
        # Cyrillic block: U+0400–U+04FF
        elif 0x0400 <= cp <= 0x04FF:
            cyrillic_count += 1

    total = len(text.replace(" ", ""))
    if total == 0:
        return None

    if arabic_count / max(total, 1) >= 0.4:
        if has_persian:
            return "fa"
        if has_arabic_exclusive:
            return "ar"
        # Ambiguous (سلام، مرحبا، etc. shared by both scripts) → default to fa
        return "fa"
    if cyrillic_count / max(total, 1) >= 0.4:
        return "ru"
    return None


async def detect_language(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return DEFAULT_LANGUAGE

    # Fast-path: script detection works for any length (even 1 char)
    script_lang = _detect_script(text)
    if script_lang:
        return script_lang

    # For short latin-script texts (< 5 chars) langdetect is unreliable → keep default
    if len(text) < 5:
        return DEFAULT_LANGUAGE

    text_hash = hashlib.md5(text[:100].encode()).hexdigest()
    cache_key = f"lang:{text_hash}"

    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        detected = detect(text)
        lang = detected if detected in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    except LangDetectException:
        lang = DEFAULT_LANGUAGE

    await cache_set(cache_key, lang, ttl=86400)
    return lang


def get_language_name(code: str) -> str:
    return SUPPORTED_LANGUAGES.get(code, "English")
