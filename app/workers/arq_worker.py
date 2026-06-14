from arq import cron
from arq.connections import RedisSettings
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.workers.tasks.monitoring import task_system_health_check, task_collect_metrics
from app.workers.tasks.publishing import task_process_scheduled_posts
from app.workers.tasks.followup import task_process_followups
from app.workers.tasks.learning import task_analyze_conversations
import urllib.parse

logger = get_logger(__name__)


async def startup(ctx):
    setup_logging()
    from app.cache.redis_client import get_redis
    from app.db.session import init_db
    await get_redis()
    await init_db()
    logger.info("arq_worker_started")


async def shutdown(ctx):
    from app.cache.redis_client import close_redis
    await close_redis()
    logger.info("arq_worker_stopped")


def _parse_redis_settings(url: str) -> RedisSettings:
    parsed = urllib.parse.urlparse(url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int(parsed.path.lstrip("/") or 1),
        password=parsed.password,
    )


class WorkerSettings:
    functions = [
        task_system_health_check,
        task_collect_metrics,
        task_process_scheduled_posts,
        task_process_followups,
        task_analyze_conversations,
    ]

    cron_jobs = [
        cron(task_collect_metrics, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),
        cron(task_system_health_check, minute={0, 30}),
        cron(task_process_scheduled_posts, minute={0, 15, 30, 45}),
        cron(task_process_followups, hour={9, 14, 18}, minute={0}),
        cron(task_analyze_conversations, hour={3}, minute={0}),
    ]

    redis_settings = _parse_redis_settings(settings.REDIS_QUEUE_URL)
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 25
    job_timeout = 300
    keep_result = 3600
    retry_jobs = True
    max_tries = 3
