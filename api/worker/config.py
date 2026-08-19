from arq import create_pool, cron
from arq.connections import RedisSettings
from setting import settings
from worker.tasks import (
    send_push_notification,
    notify_staff_store,
    notify_owner,
    notify_store,
    notify_low_stock,
    notify_credit_sale,
    notify_staff_login,
    cron_daily_sales_digest,
    cron_prune_expired_sessions,
)

REDIS_SETTINGS = RedisSettings.from_dsn(settings.REDIS_URL)

_pool = None


async def get_arq_pool():
    global _pool
    if _pool is None:
        _pool = await create_pool(REDIS_SETTINGS)
    return _pool


async def startup(ctx: dict):
    pass


async def shutdown(ctx: dict):
    pass


class WorkerSettings:
    functions = [
        send_push_notification,
        notify_staff_store,
        notify_owner,
        notify_store,
        notify_low_stock,
        notify_credit_sale,
        notify_staff_login,
        cron_daily_sales_digest,
        cron_prune_expired_sessions,
    ]
    poll_delay = 12.0
    cron_jobs = [
        cron(cron_daily_sales_digest, hour=22, minute=0),
        cron(cron_prune_expired_sessions, minute=0),
    ]
    redis_settings = REDIS_SETTINGS
    on_startup = startup
    on_shutdown = shutdown
