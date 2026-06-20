import asyncio
  import sys
  from contextlib import asynccontextmanager
  from fastapi import FastAPI

  _import_error: str = ""
  _startup_errors: list[str] = []
  _FULL_MODE = False

  # ─── Attempt all module-level imports ───────────────────────────────────────
  try:
      from fastapi import Request
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
      _FULL_MODE = True
  except Exception as _e:
      _import_error = f"{type(_e).__name__}: {_e}"
      print(f"FATAL_IMPORT_ERROR: {_import_error}", file=sys.stderr, flush=True)
      # Minimal stub so the rest of this module can reference these names
      class _FakeSettings:
          APP_NAME = "TelegramAgent"
          APP_ENV = "production"
          DEBUG = False
          DATABASE_SSL = False
          DATABASE_URL = ""
          GROQ_API_KEY = ""
          ADMIN_BOT_TOKEN = ""
          REDIS_URL = ""
          cors_origins_list = ["*"]
      settings = _FakeSettings()
      import logging as _logging
      logger = _logging.getLogger(__name__)

  _userbot_task: asyncio.Task | None = None
  _auto_poster_task: asyncio.Task | None = None


  @asynccontextmanager
  async def lifespan(app: FastAPI):
      global _userbot_task, _auto_poster_task, _startup_errors
      _startup_errors = []

      if not _FULL_MODE:
          msg = f"import_failed: {_import_error}"
          _startup_errors.append(msg)
          print(f"STARTUP_ERROR {msg}", file=sys.stderr, flush=True)
          yield
          return

      logger.info("application_starting", env=settings.APP_ENV)

      try:
          await get_redis()
          logger.info("redis_connected")
      except Exception as e:
          msg = f"redis: {e}"
          _startup_errors.append(msg)
          print(f"STARTUP_ERROR {msg}", file=sys.stderr, flush=True)

      try:
          await init_db()
          logger.info("database_initialized")
      except Exception as e:
          msg = f"init_db: {e}"
          _startup_errors.append(msg)
          print(f"STARTUP_ERROR {msg}", file=sys.stderr, flush=True)

      try:
          await userbot_manager.start()
          _userbot_task = asyncio.create_task(userbot_manager.run_until_disconnected())
          logger.info("userbot_manager_started")
      except Exception as e:
          msg = f"userbot: {e}"
          _startup_errors.append(msg)
          print(f"STARTUP_ERROR {msg}", file=sys.stderr, flush=True)

      try:
          from app.services.channel.publisher import set_userbot_manager as set_publisher_manager
          set_publisher_manager(userbot_manager)
      except Exception as e:
          _startup_errors.append(f"publisher: {e}")

      try:
          from app.services.admin_bot.bot import setup_admin_bot
          await setup_admin_bot(userbot_manager)
      except Exception as e:
          msg = f"admin_bot: {e}"
          _startup_errors.append(msg)
          print(f"STARTUP_ERROR {msg}", file=sys.stderr, flush=True)

      try:
          from app.services.channel.auto_poster import run_auto_poster
          _auto_poster_task = asyncio.create_task(run_auto_poster(userbot_manager))
          logger.info("auto_poster_started")
      except Exception as e:
          _startup_errors.append(f"auto_poster: {e}")

      if _startup_errors:
          print(f"STARTUP_ERRORS: {_startup_errors}", file=sys.stderr, flush=True)
      else:
          logger.info("application_ready")

      yield

      # ─── Shutdown ────────────────────────────────────────────────────────────
      if not _FULL_MODE:
          return
      logger.info("application_shutting_down")
      for task in (_auto_poster_task, _userbot_task):
          if task:
              task.cancel()
              try:
                  await task
              except asyncio.CancelledError:
                  pass
      try:
          await userbot_manager.stop()
      except Exception:
          pass
      try:
          from app.services.admin_bot.bot import shutdown_admin_bot
          await shutdown_admin_bot()
      except Exception:
          pass
      try:
          await close_redis()
      except Exception:
          pass
      logger.info("application_stopped")


  app = FastAPI(
      title=settings.APP_NAME,
      version="1.0.0",
      docs_url="/api/docs" if settings.DEBUG else None,
      redoc_url="/api/redoc" if settings.DEBUG else None,
      lifespan=lifespan,
  )

  if _FULL_MODE:
      try:
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
      except Exception as _e2:
          print(f"APP_SETUP_ERROR: {_e2}", file=sys.stderr, flush=True)
          _startup_errors.append(f"app_setup: {_e2}")


  @app.get("/api/healthz")
  async def healthz():
      return {"status": "ok", "app": settings.APP_NAME}


  @app.get("/api/startup-status")
  async def startup_status():
      return {
          "status": "degraded" if (_startup_errors or _import_error) else "ok",
          "import_error": _import_error,
          "startup_errors": _startup_errors,
          "full_mode": _FULL_MODE,
          "env": {
              "APP_ENV": settings.APP_ENV,
              "DATABASE_URL_set": bool(settings.DATABASE_URL),
              "GROQ_KEY_set": bool(settings.GROQ_API_KEY),
              "ADMIN_TOKEN_set": bool(settings.ADMIN_BOT_TOKEN),
              "REDIS_URL": settings.REDIS_URL,
          },
      }


  @app.api_route("/", methods=["GET", "HEAD"])
  async def health_root():
      return {"status": "ok", "app": settings.APP_NAME}


  @app.api_route("/health", methods=["GET", "HEAD"])
  async def health_check():
      return {"status": "ok", "app": settings.APP_NAME}
  