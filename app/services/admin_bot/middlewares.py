from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from app.core.config import settings
from app.core.logging import get_logger
from typing import Callable, Dict, Any, Awaitable

logger = get_logger(__name__)


class AdminOnlyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user

        if not user:
            return

        admin_ids = settings.admin_ids
        if user.id not in admin_ids:
            logger.warning("unauthorized_admin_access", user_id=user.id, username=user.username)
            if isinstance(event, Message):
                await event.answer("⛔ Unauthorized. This bot is for admins only.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Unauthorized.", show_alert=True)
            return

        data["admin_id"] = user.id
        return await handler(event, data)
