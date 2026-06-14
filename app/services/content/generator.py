from app.services.ai.engine import generate_content
from app.services.content.templates import get_content_prompt, get_all_content_types
from app.core.logging import get_logger
from typing import Optional
import asyncio

logger = get_logger(__name__)

SUPPORTED_LANGUAGES = ["en", "fa", "ar", "tr", "ru", "de", "fr", "es"]

HASHTAG_MAP = {
    "en": ["#VPS", "#CloudHosting", "#DedicatedServer", "#Hosting", "#Linux", "#DevOps", "#Server", "#WebHosting"],
    "fa": ["#VPS", "#هاستینگ_ابری", "#سرور_اختصاصی", "#هاستینگ", "#میزبانی_وب"],
    "ar": ["#VPS", "#استضافة_سحابية", "#خادم_مخصص", "#استضافة"],
    "tr": ["#VPS", "#BulutHosting", "#DedicatedSunucu", "#Hosting"],
    "ru": ["#VPS", "#ОблачныйХостинг", "#ВыделенныйСервер", "#Хостинг"],
    "de": ["#VPS", "#CloudHosting", "#DedicatedServer", "#Hosting"],
    "fr": ["#VPS", "#HébergementCloud", "#ServeurDédié", "#Hébergement"],
    "es": ["#VPS", "#AlojamientoCloud", "#ServidorDedicado", "#Hosting"],
}


async def generate_post(
    content_type: str,
    topic: str,
    language: str = "en",
    include_hashtags: bool = True,
) -> str:
    prompt = get_content_prompt(content_type, topic, language)
    try:
        content = await generate_content(prompt)
        if include_hashtags:
            tags = _pick_hashtags(topic, language, count=4)
            if tags:
                content = f"{content}\n\n{' '.join(tags)}"
        logger.info("post_generated", content_type=content_type, language=language, topic=topic)
        return content
    except Exception as e:
        logger.error("post_generation_failed", error=str(e), topic=topic)
        raise


async def generate_multilingual_post(
    content_type: str,
    topic: str,
    languages: list[str] = None,
    include_hashtags: bool = True,
) -> dict[str, str]:
    languages = [lang for lang in (languages or ["en"]) if lang in SUPPORTED_LANGUAGES]
    if not languages:
        languages = ["en"]

    tasks = {
        lang: generate_post(content_type, topic, lang, include_hashtags)
        for lang in languages
    }

    results = {}
    completed = await asyncio.gather(*tasks.values(), return_exceptions=True)
    for lang, result in zip(tasks.keys(), completed):
        if isinstance(result, Exception):
            logger.error("multilingual_post_failed", lang=lang, error=str(result))
            results[lang] = f"[Generation failed for {lang}]"
        else:
            results[lang] = result

    return results


async def generate_post_variants(
    content_type: str,
    topic: str,
    language: str = "en",
    count: int = 2,
) -> list[str]:
    tasks = [generate_post(content_type, topic, language, include_hashtags=False) for _ in range(count)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    variants = []
    for r in results:
        if not isinstance(r, Exception):
            variants.append(r)
    return variants


def _pick_hashtags(topic: str, language: str, count: int = 4) -> list[str]:
    base = HASHTAG_MAP.get(language, HASHTAG_MAP["en"])
    topic_tags = []
    topic_words = topic.lower().split()
    for word in topic_words:
        if len(word) > 3:
            tag = f"#{word.capitalize()}"
            if tag not in base:
                topic_tags.append(tag)
    combined = base[:count - len(topic_tags[:1])] + topic_tags[:1]
    return combined[:count]


def get_supported_languages() -> list[str]:
    return SUPPORTED_LANGUAGES


def get_content_types() -> list[str]:
    return get_all_content_types()
