from arq import create_pool
from setting import settings
from arq.worker import WorkerSettingsType
from arq.connections import RedisSettings

REDIS_SETTINGS = RedisSettings.from_dsn(settings.REDIS_URL)

async def arq_pool():
    pool = await create_pool(REDIS_SETTINGS)
    return pool


class WorkerSettings:
    functions = []
    redis_settings = REDIS_SETTINGS
