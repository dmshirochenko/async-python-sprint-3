import asyncpg
import asyncio
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def retry_database_connection(max_attempts=5, retry_interval=5):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(self, *args, **kwargs)
                except (OSError, asyncpg.PostgresError) as e:
                    last_exception = e
                    logger.error("Attempt %d failed: %s", attempt, e)
                    if attempt < max_attempts:
                        await asyncio.sleep(retry_interval)
            raise last_exception

        return wrapper

    return decorator
