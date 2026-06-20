from telethon import TelegramClient
from telethon.sessions import StringSession
from app.core.config import settings
from app.core.logging import get_logger
from app.services.userbot.session_manager import get_session_path
from typing import Optional

logger = get_logger(__name__)


class UserBotClient:
    def __init__(self, phone: str, session_string: Optional[str] = None, account_id: str = None):
        self.phone = phone
        self.account_id = account_id
        self._is_connected = False

        if session_string:
            session = StringSession(session_string)
        else:
            session = get_session_path(phone)

        self._client = TelegramClient(
            session,
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH,
            device_model="Linux Server",
            system_version="Ubuntu 22.04",
            app_version="1.0.0",
            lang_code="en",
            system_lang_code="en",
            # Limit retries so startup does not hang
            connection_retries=1,
            retry_delay=1,
            timeout=10,
            request_retries=1,
            flood_sleep_threshold=0,
        )

    @property
    def client(self) -> TelegramClient:
        return self._client

    async def connect(self) -> bool:
        try:
            await self._client.connect()
            if not await self._client.is_user_authorized():
                logger.warning("userbot_not_authorized", phone=self.phone)
                return False
            me = await self._client.get_me()
            self._is_connected = True
            logger.info("userbot_connected", phone=self.phone, name=f"{me.first_name}")
            return True
        except Exception as e:
            logger.error("userbot_connect_failed", phone=self.phone, error=str(e))
            return False

    async def disconnect(self) -> None:
        if self._client.is_connected():
            await self._client.disconnect()
            self._is_connected = False
            logger.info("userbot_disconnected", phone=self.phone)

    async def send_message(self, entity, text: str, parse_mode: str = "md"):
        return await self._client.send_message(entity, text, parse_mode=parse_mode)

    async def send_file(self, entity, file, caption: str = None, parse_mode: str = "md"):
        return await self._client.send_file(
            entity,
            file,
            caption=caption,
            parse_mode=parse_mode,
        )

    async def get_me(self):
        return await self._client.get_me()

    @property
    def is_connected(self) -> bool:
        return self._is_connected and self._client.is_connected()
