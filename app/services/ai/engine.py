from openai import AsyncOpenAI
from app.core.config import settings
from app.core.logging import get_logger
from typing import Optional, List, AsyncIterator
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import asyncio

logger = get_logger(__name__)
_client: Optional[AsyncOpenAI] = None


def get_ai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if settings.GROQ_API_KEY:
            _client = AsyncOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url=settings.GROQ_BASE_URL,
                timeout=60.0,
                max_retries=0,
            )
            logger.info("ai_provider_groq", model=settings.GROQ_MODEL)
        else:
            _client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=60.0,
                max_retries=0,
            )
            logger.info("ai_provider_openai", model=settings.OPENAI_MODEL)
    return _client


def get_model() -> str:
    return settings.GROQ_MODEL if settings.GROQ_API_KEY else settings.OPENAI_MODEL


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def generate_reply(
    messages: List[dict],
    system_prompt: str,
    temperature: float = None,
    max_tokens: int = None,
    tools: List[dict] = None,
) -> tuple[str, int]:
    client = get_ai_client()
    temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE
    max_tokens = max_tokens or settings.OPENAI_MAX_TOKENS

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    kwargs = dict(
        model=get_model(),
        messages=full_messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    try:
        response = await client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        logger.info("ai_reply_generated", tokens=tokens, model=get_model())
        return content, tokens
    except Exception as e:
        logger.error("ai_generation_failed", error=str(e))
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def generate_content(prompt: str, system: str = "", temperature: float = 0.8) -> str:
    client = get_ai_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=get_model(),
        messages=messages,
        temperature=temperature,
        max_tokens=2000,
    )
    return response.choices[0].message.content or ""


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5))
async def generate_embedding(text: str) -> List[float]:
    if settings.GROQ_API_KEY and not settings.OPENAI_API_KEY:
        logger.warning("embeddings_not_supported_on_groq_returning_empty")
        return []
    client = get_ai_client()
    text = text.replace("\n", " ")[:8000]
    try:
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error("embedding_generation_failed", error=str(e))
        return []


async def generate_reply_streaming(
    messages: List[dict],
    system_prompt: str,
    temperature: float = None,
    max_tokens: int = None,
) -> AsyncIterator[str]:
    client = get_ai_client()
    temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE
    max_tokens = max_tokens or settings.OPENAI_MAX_TOKENS

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    try:
        stream = await client.chat.completions.create(
            model=get_model(),
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:
        logger.error("ai_streaming_failed", error=str(e))
        raise


async def extract_facts_from_conversation(messages: List[dict], language: str = "en") -> dict:
    system = """Extract key facts about the customer from this conversation.
Return ONLY valid JSON with these keys:
- budget_min: number or null
- budget_max: number or null  
- use_case: string or null (e.g. "wordpress", "game server", "e-commerce")
- tech_level: one of ["beginner", "intermediate", "expert"] or null
- team_size: number or null
- current_provider: string or null
- pain_points: list of strings
- preferred_os: string or null
- location_mentioned: string or null
- timeline: string or null (e.g. "urgent", "within a week", "exploring")
"""
    try:
        conv_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages[-20:]])
        result, _ = await generate_reply(
            [{"role": "user", "content": conv_text}],
            system,
            temperature=0.1,
            max_tokens=400,
        )
        import json, re
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        logger.warning("fact_extraction_failed", error=str(e))
    return {}


async def check_ai_health() -> bool:
    try:
        client = get_ai_client()
        await client.chat.completions.create(
            model=get_model(),
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        return True
    except Exception as e:
        logger.error("ai_health_check_failed", error=str(e))
        return False
