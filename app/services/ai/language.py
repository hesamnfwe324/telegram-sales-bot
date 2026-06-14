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


async def detect_language(text: str) -> str:
    if not text or len(text.strip()) < 5:
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
