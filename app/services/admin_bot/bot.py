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


async def setup_admin_bot(userbot_manager=None) -> None:
    bot = get_bot()
    dp = get_dispatcher()

    if userbot_manager:
        control.set_userbot_manager(userbot_manager)

    alerts.set_bot(bot)

    from app.services.monitoring.alerting import set_alert_sender
    async def send_to_admins(text: str):
        await alerts.broadcast_alert(text)
    set_alert_sender(send_to_admins)

    # Always use polling mode (webhook requires proxy routing not available here)
    try:
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("admin_bot_webhook_deleted")
    except Exception as e:
        logger.warning("admin_bot_webhook_delete_failed", error=str(e))

    import asyncio
    asyncio.create_task(_run_polling(bot, dp))
    logger.info("admin_bot_started")


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
        await bot.delete_webhook()
        await bot.session.close()
        logger.info("admin_bot_shutdown")
    except Exception as e:
        logger.error("admin_bot_shutdown_error", error=str(e))
