import asyncpg
import asyncio
from functools import wraps
import logging


def retry_database_connection(max_attempts=5, retry_interval=5):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(self, *args, **kwargs)
                except (OSError, asyncpg.exceptions.CannotConnectNowError) as e:
                    last_exception = e
                    logging.error(f"Attempt {attempt} failed: {e}")
                    if attempt < max_attempts:
                        await asyncio.sleep(retry_interval)
            raise last_exception

        return wrapper

    return decorator
