from app.core.config import settings
from app.core.logging import get_logger
from app.services.monitoring.metrics_collector import collect_system_metrics
from app.db.session import AsyncSessionLocal
from app.models.alert import Alert
from app.cache.redis_client import cache_get, cache_set
from datetime import datetime, timezone
import asyncio

logger = get_logger(__name__)

_admin_bot_send_func = None

SEVERITY_EMOJI = {
    "critical": "🔴",
    "warning": "🟡",
    "info": "🔵",
    "success": "🟢",
}

COOLDOWN_TTL = 300


def set_alert_sender(func) -> None:
    global _admin_bot_send_func
    _admin_bot_send_func = func


async def _is_on_cooldown(alert_key: str) -> bool:
    key = f"alert_cooldown:{alert_key}"
    return bool(await cache_get(key))


async def _set_cooldown(alert_key: str, ttl: int = COOLDOWN_TTL) -> None:
    key = f"alert_cooldown:{alert_key}"
    await cache_set(key, True, ttl=ttl)


async def send_alert(
    severity: str,
    alert_type: str,
    message: str,
    context: dict = None,
    cooldown: bool = True,
) -> None:
    cooldown_key = f"{alert_type}:{message[:40]}"
    if cooldown and await _is_on_cooldown(cooldown_key):
        logger.debug("alert_suppressed_cooldown", key=cooldown_key)
        return

    async with AsyncSessionLocal() as session:
        session.add(Alert(
            type=alert_type,
            severity=severity,
            message=message,
            context=context or {},
        ))
        await session.commit()

    logger.warning("alert_created", severity=severity, type=alert_type, message=message)

    if cooldown:
        await _set_cooldown(cooldown_key)

    if _admin_bot_send_func:
        emoji = SEVERITY_EMOJI.get(severity, "⚪")
        ctx_str = ""
        if context:
            ctx_lines = [f"  `{k}`: {v}" for k, v in list(context.items())[:4]]
            ctx_str = "\n" + "\n".join(ctx_lines)
        text = (
            f"{emoji} *{severity.upper()} — {alert_type.upper()}*\n\n"
            f"{message}{ctx_str}\n\n"
            f"_🕐 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_"
        )
        try:
            await _admin_bot_send_func(text)
        except Exception as e:
            logger.error("alert_send_failed", error=str(e))


async def check_system_thresholds() -> None:
    metrics = await collect_system_metrics()

    cpu = metrics["cpu_percent"]
    ram_pct = metrics["ram"]["percent"]
    disk_pct = metrics["disk"]["percent"]

    if cpu > settings.ALERT_CPU_THRESHOLD:
        severity = "critical" if cpu > 95 else "warning"
        await send_alert(
            severity, "system",
            f"CPU usage {severity}: {cpu:.1f}%",
            {"cpu": cpu, "threshold": settings.ALERT_CPU_THRESHOLD},
        )

    if ram_pct > settings.ALERT_RAM_THRESHOLD:
        severity = "critical" if ram_pct > 95 else "warning"
        await send_alert(
            severity, "system",
            f"RAM usage {severity}: {ram_pct:.1f}%",
            {"ram_percent": ram_pct, "used_gb": metrics["ram"]["used_gb"]},
        )

    if disk_pct > settings.ALERT_DISK_THRESHOLD:
        severity = "critical" if disk_pct > 95 else "warning"
        await send_alert(
            severity, "system",
            f"Disk usage {severity}: {disk_pct:.1f}%",
            {"disk_percent": disk_pct, "used_gb": metrics["disk"]["used_gb"]},
        )


async def notify_new_hot_lead(customer_name: str, service: str, score: float) -> None:
    if score >= 0.7:
        await send_alert(
            "info", "sales",
            f"🔥 Hot lead detected! {customer_name} interested in {service.upper()} (score: {score:.0%})",
            {"customer": customer_name, "service": service, "score": score},
            cooldown=False,
        )


async def notify_account_disconnected(phone: str, account_id: str) -> None:
    await send_alert(
        "critical", "telegram",
        f"Userbot disconnected: {phone}",
        {"account_id": account_id},
        cooldown=True,
    )
