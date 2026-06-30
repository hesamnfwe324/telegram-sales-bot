import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from app.core.config import settings
from app.core.logging import get_logger
from app.services.admin_bot.middlewares import AdminOnlyMiddleware
from app.services.admin_bot.handlers import status, metrics, conversations, sales, publishing, logs, control, alerts, scanner

logger = get_logger(__name__)

_bot: Bot = None
_dp: Dispatcher = None


def get_bot() -> Bot | None:
    global _bot
    if _bot is None:
        if not settings.ADMIN_BOT_TOKEN:
            logger.warning("admin_bot_token_not_set_skipping_bot_init")
            return None
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
        _dp.include_router(scanner.router)

    return _dp


def _get_webhook_url() -> str | None:
    base = (
        os.environ.get("WEBHOOK_BASE_URL")
        or os.environ.get("RENDER_EXTERNAL_URL")
    )
    if not base:
        return None
    return base.rstrip("/") + "/tg-api/admin-bot/webhook"


async def _ensure_webhook(bot: Bot, webhook_url: str, delay: float = 20.0) -> None:
    """Re-verify webhook after a delay to survive old-deploy shutdown race."""
    await asyncio.sleep(delay)
    try:
        info = await bot.get_webhook_info()
        if info.url != webhook_url:
            logger.warning("admin_bot_webhook_lost", current=info.url, expected=webhook_url)
            await bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=False,
                allowed_updates=["message", "callback_query"],
            )
            logger.info("admin_bot_webhook_reapplied", url=webhook_url)
        else:
            logger.info("admin_bot_webhook_verified_ok", url=webhook_url)
    except Exception as e:
        logger.error("admin_bot_webhook_verify_failed", error=str(e))


async def setup_admin_bot(userbot_manager=None) -> None:
    bot = get_bot()
    if bot is None:
        logger.warning("admin_bot_disabled_no_token")
        return
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
            asyncio.create_task(_ensure_webhook(bot, webhook_url, delay=20.0))
        except Exception as e:
            logger.error("admin_bot_set_webhook_failed", error=str(e))
            asyncio.create_task(_run_polling(bot, dp))
    else:
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
    if bot is None:
        return
    dp = get_dispatcher()
    update = Update.model_validate(update_data)
    await dp.feed_update(bot, update)


async def shutdown_admin_bot() -> None:
    """Graceful shutdown — does NOT delete_webhook.

    Deleting the webhook here would break rolling deploys: the new instance
    already called set_webhook before this instance shuts down.
    """
    bot = get_bot()
    if bot is None:
        return
    try:
        await bot.session.close()
        logger.info("admin_bot_shutdown")
    except Exception as e:
        logger.error("admin_bot_shutdown_error", error=str(e))
