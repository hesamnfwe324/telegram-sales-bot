from langdetect import detect, LangDetectException
from app.core.logging import get_logger
import hashlib
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

_PERSIAN_EXCLUSIVE = set("پچژگکی‌")


def _detect_script(text: str) -> str | None:
    arabic_count = 0
    cyrillic_count = 0
    has_persian = False
    for ch in text:
        if ch in _PERSIAN_EXCLUSIVE:
            has_persian = True
        cp = ord(ch)
        if 0x0600 <= cp <= 0x06FF:
            arabic_count += 1
        elif 0x0400 <= cp <= 0x04FF:
            cyrillic_count += 1
    total = len(text.replace(" ", ""))
    if total == 0:
        return None
    if arabic_count / max(total, 1) >= 0.4:
        return "fa" if has_persian else "ar"
    if cyrillic_count / max(total, 1) >= 0.4:
        return "ru"
    return None


async def detect_language(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return DEFAULT_LANGUAGE
    script_lang = _detect_script(text)
    if script_lang:
        return script_lang
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
