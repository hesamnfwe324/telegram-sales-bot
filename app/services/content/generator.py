from app.services.ai.engine import generate_content
from app.services.content.templates import get_content_prompt, get_all_content_types
from app.core.logging import get_logger
from typing import Optional
import asyncio
import random

logger = get_logger(__name__)

SUPPORTED_LANGUAGES = ["en", "fa", "ar", "tr", "ru", "de", "fr", "es"]

HASHTAG_MAP = {
    "en": ["#VPS", "#CloudHosting", "#DedicatedServer", "#Hosting", "#Linux",
           "#DevOps", "#Server", "#WebHosting", "#SysAdmin", "#TechTips"],
    "fa": ["#VPS", "#هاستینگ_ابری", "#سرور_اختصاصی", "#هاستینگ", "#میزبانی_وب", "#لینوکس"],
    "ar": ["#VPS", "#استضافة_سحابية", "#خادم_مخصص", "#استضافة", "#لينكس"],
    "tr": ["#VPS", "#BulutHosting", "#DedicatedSunucu", "#Hosting", "#Linux"],
    "ru": ["#VPS", "#ОблачныйХостинг", "#ВыделенныйСервер", "#Хостинг", "#Linux"],
    "de": ["#VPS", "#CloudHosting", "#DedicatedServer", "#Hosting", "#Linux"],
    "fr": ["#VPS", "#HébergementCloud", "#ServeurDédié", "#Hébergement", "#Linux"],
    "es": ["#VPS", "#AlojamientoCloud", "#ServidorDedicado", "#Hosting", "#Linux"],
}


async def generate_post(
    content_type: str,
    topic: str,
    language: str = "en",
    include_hashtags: bool = True,
    style_hint: str = "",
    forbidden_angles: list[str] | None = None,
    unique_seed: int | None = None,
) -> str:
    prompt = get_content_prompt(
        content_type, topic, language,
        style_hint=style_hint,
        forbidden_angles=forbidden_angles or [],
        unique_seed=unique_seed,
    )
    try:
        content = await generate_content(prompt)
        if include_hashtags:
            tags = _pick_hashtags(topic, language, count=4)
            if tags:
                content = f"{content}\n\n{' '.join(tags)}"
        logger.info("post_generated", content_type=content_type,
                    language=language, topic=topic)
        return content
    except Exception as e:
        logger.error("post_generation_failed", error=str(e), topic=topic)
        raise


async def generate_multilingual_post(
    content_type: str,
    topic: str,
    languages: list[str] | None = None,
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
    tasks = [
        generate_post(content_type, topic, language, include_hashtags=False)
        for _ in range(count)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]


def _pick_hashtags(topic: str, language: str, count: int = 4) -> list[str]:
    base = HASHTAG_MAP.get(language, HASHTAG_MAP["en"])
    shuffled = random.sample(base, min(len(base), count))
    topic_tags = []
    for word in topic.lower().split():
        if len(word) > 4:
            tag = f"#{word.capitalize()}"
            if tag not in shuffled:
                topic_tags.append(tag)
    combined = shuffled[:count - len(topic_tags[:1])] + topic_tags[:1]
    return combined[:count]


def get_supported_languages() -> list[str]:
    return SUPPORTED_LANGUAGES


def get_content_types() -> list[str]:
    return get_all_content_types()
