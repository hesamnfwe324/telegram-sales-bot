import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from app.core.config import settings
from app.core.logging import get_logger
from app.services.admin_bot.middlewares import AdminOnlyMiddleware
from app.services.admin_bot.handlers import status, metrics, conversations, sales, publishing, logs, control, alerts

logger = get_logger(__name__)

_bot: Bot = None
_dp: Dispatcher = None


def get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(
            token=settings.ADMIN_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
        )
    return _bot


def get_dispatcher() -> Dispatcher:
    global _dp
    if _dp is None:
        _dp = Dispatcher(storage=MemoryStorage())
        _dp.message.middleware(AdminOnlyMiddleware())
        _dp.callback_query.middleware(AdminOnlyMiddleware())

        _dp.include_router(status.router)
        _dp.include_router(metrics.router)
        _dp.include_router(conversations.router)
        _dp.include_router(sales.router)
        _dp.include_router(publishing.router)
        _dp.include_router(logs.router)
        _dp.include_router(control.router)
        _dp.include_router(alerts.router)

    return _dp


def _get_webhook_url() -> str | None:
    """
    Return the full webhook URL when running on Render (or any host that
    sets RENDER_EXTERNAL_URL / WEBHOOK_BASE_URL).
    Returns None when running locally → fall back to polling.
    """
    base = (
        os.environ.get("WEBHOOK_BASE_URL")       # manual override
        or os.environ.get("RENDER_EXTERNAL_URL")  # auto-set by Render
    )
    if not base:
        return None
    base = base.rstrip("/")
    return f"{base}/tg-api/admin-bot/webhook"


async def setup_admin_bot(userbot_manager=None) -> None:
    import asyncio

    bot = get_bot()
    dp = get_dispatcher()

    if userbot_manager:
        control.set_userbot_manager(userbot_manager)

    alerts.set_bot(bot)

    from app.services.monitoring.alerting import set_alert_sender
    async def send_to_admins(text: str):
        await alerts.broadcast_alert(text)
    set_alert_sender(send_to_admins)

    webhook_url = _get_webhook_url()

    if webhook_url:
        # ── Webhook mode (production / Render) ─────────────────────────
        # Drop any pending updates so the new instance starts clean,
        # then register the webhook. No polling → no ConflictError.
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("admin_bot_old_webhook_cleared")
        except Exception as e:
            logger.warning("admin_bot_delete_webhook_failed", error=str(e))

        try:
            await bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"],
            )
            logger.info("admin_bot_webhook_set", url=webhook_url)
        except Exception as e:
            logger.error("admin_bot_set_webhook_failed", error=str(e))
            # Fall back to polling if webhook setup fails
            asyncio.create_task(_run_polling(bot, dp))
    else:
        # ── Polling mode (local development) ───────────────────────────
        try:
            await bot.delete_webhook(drop_pending_updates=True)
        except Exception:
            pass
        asyncio.create_task(_run_polling(bot, dp))
        logger.info("admin_bot_polling_started_local")

    logger.info("admin_bot_setup_complete", mode="webhook" if webhook_url else "polling")


async def _run_polling(bot: Bot, dp: Dispatcher) -> None:
    try:
        logger.info("admin_bot_polling_starting")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logger.error("admin_bot_polling_error", error=str(e))


async def process_update(update_data: dict) -> None:
    bot = get_bot()
    dp = get_dispatcher()
    update = Update.model_validate(update_data)
    await dp.feed_update(bot, update)


async def shutdown_admin_bot() -> None:
    bot = get_bot()
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        await bot.session.close()
        logger.info("admin_bot_shutdown")
    except Exception as e:
        logger.error("admin_bot_shutdown_error", error=str(e))
