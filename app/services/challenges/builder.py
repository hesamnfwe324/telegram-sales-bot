import asyncio
import json
import random
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.services.ai.engine import generate_content

logger = get_logger(__name__)

SUPPORTED_LANGUAGES = ("en", "fa", "ar", "tr", "ru", "de", "fr", "es")

_FALLBACKS: dict[str, dict[str, Any]] = {
    "en": {
        "title": "RDP Security Challenge",
        "body": (
            "You inherit a Windows RDP server. Which change should happen first?\n\n"
            "The example host is 192.0.2.10. It is documentation-only and is not a real server."
        ),
        "options": [
            "Expose RDP to the whole internet",
            "Restrict access with a VPN or allowlist and enable MFA",
            "Share the admin password in the team chat",
            "Disable all logging",
        ],
        "correct_index": 1,
        "explanation": "Reduce the attack surface first: use a private access path or allowlist, then add MFA and keep audit logs.",
    },
    "fa": {
        "title": "چالش امنیتی RDP",
        "body": (
            "یک سرور ویندوزی RDP را تحویل گرفته‌اید. اولین اقدام درست چیست؟\n\n"
            "آدرس نمونه 192.0.2.10 است و فقط برای مستندات استفاده می‌شود؛ سرور واقعی نیست."
        ),
        "options": [
            "باز گذاشتن RDP برای کل اینترنت",
            "محدودکردن دسترسی با VPN یا فهرست مجاز و فعال‌کردن MFA",
            "فرستادن رمز ادمین در گروه کاری",
            "خاموش‌کردن همه لاگ‌ها",
        ],
        "correct_index": 1,
        "explanation": "اول سطح حمله را کم کنید: دسترسی خصوصی یا فهرست مجاز، سپس MFA و نگهداری لاگ‌های ممیزی.",
    },
    "ar": {
        "title": "تحدي أمان RDP",
        "body": "استلمت خادم Windows يعمل عبر RDP. ما أول إجراء صحيح؟\n\nالعنوان 192.0.2.10 تجريبي للتوثيق وليس خادماً حقيقياً.",
        "options": ["فتح RDP للعالم", "تقييد الوصول عبر VPN أو قائمة سماح وتفعيل MFA", "مشاركة كلمة المرور", "تعطيل السجلات"],
        "correct_index": 1,
        "explanation": "قلّل سطح الهجوم أولاً، ثم فعّل المصادقة متعددة العوامل واحتفظ بسجلات التدقيق.",
    },
    "tr": {
        "title": "RDP Güvenlik Yarışması",
        "body": "Bir Windows RDP sunucusu devraldınız. İlk doğru adım hangisi?\n\n192.0.2.10 yalnızca dokümantasyon için örnektir.",
        "options": ["RDP'yi internete açmak", "VPN veya izin listesiyle erişimi sınırlayıp MFA'yı açmak", "Parolayı paylaşmak", "Tüm kayıtları kapatmak"],
        "correct_index": 1,
        "explanation": "Önce saldırı yüzeyini azaltın; ardından MFA ve denetim kayıtlarını kullanın.",
    },
    "ru": {
        "title": "Челлендж по безопасности RDP",
        "body": "Вы получили Windows-сервер с RDP. Какое действие нужно сделать первым?\n\n192.0.2.10 — учебный адрес, не реальный сервер.",
        "options": ["Открыть RDP всему интернету", "Ограничить доступ через VPN или allowlist и включить MFA", "Разослать пароль", "Отключить журналы"],
        "correct_index": 1,
        "explanation": "Сначала уменьшите поверхность атаки, затем включите MFA и аудит.",
    },
    "de": {
        "title": "RDP-Sicherheits-Challenge",
        "body": "Sie übernehmen einen Windows-RDP-Server. Was sollte zuerst passieren?\n\n192.0.2.10 ist nur eine Dokumentationsadresse.",
        "options": ["RDP für alle öffnen", "Zugriff per VPN oder Allowlist begrenzen und MFA aktivieren", "Passwort teilen", "Protokolle deaktivieren"],
        "correct_index": 1,
        "explanation": "Zuerst die Angriffsfläche reduzieren, danach MFA und Audit-Protokolle aktivieren.",
    },
    "fr": {
        "title": "Défi sécurité RDP",
        "body": "Vous récupérez un serveur Windows avec RDP. Quelle est la première action correcte ?\n\n192.0.2.10 est une adresse d'exemple.",
        "options": ["Ouvrir RDP à Internet", "Limiter l'accès par VPN ou liste blanche et activer MFA", "Partager le mot de passe", "Désactiver les journaux"],
        "correct_index": 1,
        "explanation": "Réduisez d'abord la surface d'attaque, puis activez MFA et les journaux d'audit.",
    },
    "es": {
        "title": "Reto de seguridad RDP",
        "body": "Recibes un servidor Windows con RDP. ¿Qué debes hacer primero?\n\n192.0.2.10 es una dirección de ejemplo.",
        "options": ["Exponer RDP a Internet", "Limitar el acceso con VPN o lista permitida y activar MFA", "Compartir la contraseña", "Desactivar los registros"],
        "correct_index": 1,
        "explanation": "Reduce primero la superficie de ataque y después activa MFA y los registros de auditoría.",
    },
}


def _valid_translation(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("title"), str)
        and isinstance(value.get("body"), str)
        and isinstance(value.get("options"), list)
        and len(value["options"]) == 4
        and all(isinstance(option, str) and option.strip() for option in value["options"])
        and isinstance(value.get("correct_index"), int)
        and 0 <= value["correct_index"] < 4
        and isinstance(value.get("explanation"), str)
    )


async def _build_ai_translation(language: str) -> dict[str, Any] | None:
    if not (settings.GROQ_API_KEY or settings.OPENAI_API_KEY):
        return None

    prompt = f"""
Create one safe, educational RDP security quiz in language code "{language}".
Return ONLY valid JSON with exactly these keys:
title (string), body (string), options (array of exactly 4 strings),
correct_index (integer 0-3), explanation (string).

Rules:
- Teach defensive configuration for an RDP service that the reader owns.
- Use only documentation IP 192.0.2.10 or example.com; never use a real host.
- Never include credentials, password guessing, scanning, exploitation, persistence,
  bypassing authentication, or instructions to access someone else's system.
- Make one option clearly correct and the other three plausible but unsafe.
"""
    try:
        raw = await asyncio.wait_for(
            generate_content(
                prompt,
                system="You write concise, responsible cybersecurity education for a hosting business.",
                temperature=0.6,
            ),
            timeout=20,
        )
        parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        return parsed if _valid_translation(parsed) else None
    except Exception as exc:
        logger.warning("rdp_challenge_ai_generation_failed", language=language, error=str(exc)[:160])
        return None


async def build_challenge_translations(languages: list[str]) -> tuple[dict[str, dict[str, Any]], str]:
    normalized = []
    for language in languages:
        code = (language or "en").lower()[:2]
        normalized.append(code if code in SUPPORTED_LANGUAGES else "en")
    # Always keep English available for the canonical Post.content field,
    # even when every active channel uses another language.
    normalized = list(dict.fromkeys(["en", *normalized]))

    built: dict[str, dict[str, Any]] = {}
    ai_count = 0
    for language in normalized:
        generated = await _build_ai_translation(language)
        built[language] = generated or _FALLBACKS[language]
        ai_count += int(generated is not None)

    return built, "ai" if ai_count else "fallback"


def render_translation(translation: dict[str, Any], channel_username: str | None = None) -> str:
    channel_line = f"\n\n📢 @{channel_username.lstrip('@')}" if channel_username else ""
    options = "\n".join(
        f"{index + 1}. {option}" for index, option in enumerate(translation["options"])
    )
    return (
        f"🧠 {translation['title']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{translation['body']}\n\n"
        "❓ Choose the safest answer below:\n"
        f"{options}\n\n"
        "👇 Tap an option to submit your answer."
        f"{channel_line}"
    )