from arq import create_pool, cron
from arq.connections import RedisSettings
from setting import settings
from worker.tasks import (
    send_push_notification,
    notify_staff_store,
    notify_user_personal,
    notify_low_stock,
    send_admin_email_campaign,
    send_admin_welcome_email,
    send_auth_reset_email,
    cron_generate_daily_metrics,
    cron_cleanup_expired_sessions,
    process_inbound_resend_email,
    process_resend_event,
    sync_outgoing_email_message_id,
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
        notify_user_personal,
        notify_low_stock,
        send_admin_email_campaign,
        send_admin_welcome_email,
        send_auth_reset_email,
        cron_generate_daily_metrics,
        cron_cleanup_expired_sessions,
        process_inbound_resend_email,
        process_resend_event,
        sync_outgoing_email_message_id,
    ]
    poll_delay = 1
    cron_jobs = [
        cron(cron_cleanup_expired_sessions, minute=0),
        cron(cron_generate_daily_metrics, hour=23, minute=55),
    ]
    redis_settings = REDIS_SETTINGS
    on_startup = startup
    on_shutdown = shutdown
