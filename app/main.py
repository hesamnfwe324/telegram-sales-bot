import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import AppException
from app.db.session import init_db
from app.cache.redis_client import get_redis, close_redis
from app.services.userbot.manager import userbot_manager
from app.api.v1 import customers, conversations, leads, content, channels, accounts, knowledge, metrics

setup_logging()
logger = get_logger(__name__)

_userbot_task: asyncio.Task | None = None
_auto_poster_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _userbot_task, _auto_poster_task

    logger.info("application_starting", env=settings.APP_ENV)

    await get_redis()
    logger.info("redis_connected")

    await init_db()
    logger.info("database_initialized")

    await userbot_manager.start()
    _userbot_task = asyncio.create_task(userbot_manager.run_until_disconnected())
    logger.info("userbot_manager_started")

    from app.services.channel.publisher import set_userbot_manager as set_publisher_manager
    set_publisher_manager(userbot_manager)

    from app.services.admin_bot.bot import setup_admin_bot
    await setup_admin_bot(userbot_manager)

    from app.services.channel.auto_poster import run_auto_poster
    _auto_poster_task = asyncio.create_task(run_auto_poster(userbot_manager))
    logger.info("auto_poster_started")

    logger.info("application_ready")
    yield

    logger.info("application_shutting_down")
    if _auto_poster_task:
        _auto_poster_task.cancel()
        try:
            await _auto_poster_task
        except asyncio.CancelledError:
            pass
    if _userbot_task:
        _userbot_task.cancel()
        try:
            await _userbot_task
        except asyncio.CancelledError:
            pass
    await userbot_manager.stop()

    from app.services.admin_bot.bot import shutdown_admin_bot
    await shutdown_admin_bot()

    await close_redis()  # Redis closed AFTER admin bot — bot may send shutdown alerts
    logger.info("application_stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=400,
        content={"error": exc.code, "message": exc.message},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
    )


@app.post("/tg-api/admin-bot/webhook")
async def admin_bot_webhook(request: Request):
    try:
        update_data = await request.json()
        from app.services.admin_bot.bot import process_update
        await process_update(update_data)
    except Exception as e:
        logger.error("webhook_processing_error", error=str(e))
    return {"ok": True}


API_PREFIX = "/api/v1"
app.include_router(customers.router, prefix=API_PREFIX)
app.include_router(conversations.router, prefix=API_PREFIX)
app.include_router(leads.router, prefix=API_PREFIX)
app.include_router(content.router, prefix=API_PREFIX)
app.include_router(channels.router, prefix=API_PREFIX)
app.include_router(accounts.router, prefix=API_PREFIX)
app.include_router(knowledge.router, prefix=API_PREFIX)
app.include_router(metrics.router, prefix=API_PREFIX)


@app.get("/api/healthz")
async def healthz():
    return {"status": "ok", "app": settings.APP_NAME}
