import asyncpg
import logging.config
from typing import Any, Optional

from config.logger import LOGGING
from src.backoff.backoff import retry_database_connection

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


class AsyncDatabaseConnector:
    def __init__(self, database_url: str) -> None:
        self.database_url: str = database_url
        self.connection: Optional[asyncpg.Connection] = None

    async def _establish_connection(self) -> None:
        try:
            if self.connection is None or self.connection.is_closed():
                self.connection = await asyncpg.connect(self.database_url)
        except asyncpg.PostgresError as e:
            logger.error("Error establishing database connection: %s", e)
            raise e

    @retry_database_connection()
    async def connect(self) -> None:
        try:
            self.connection = await asyncpg.connect(self.database_url)
        except asyncpg.PostgresError as e:
            logger.error("Error connecting to database: %s", e)
            raise e

    async def close(self) -> None:
        if self.connection:
            await self.connection.close()

    async def execute(self, query: str, *args: Any, **kwargs: Any) -> str:
        try:
            if not self.connection:
                await self.connect()
            if kwargs:
                return await self.connection.execute(query, *args, **kwargs)
            else:
                return await self.connection.execute(query, *args)
        except asyncpg.PostgresError as e:
            logger.error("Error executing query: %s", e)
            raise e

    async def fetch(self, query: str, *args: Any) -> list:
        try:
            if not self.connection:
                await self.connect()
            return await self.connection.fetch(query, *args)
        except asyncpg.PostgresError as e:
            logger.error("Error fetching data: %s", e)
            raise e

    async def fetchrow(self, query: str, *args: Any) -> asyncpg.Record:
        try:
            if not self.connection:
                await self.connect()
            return await self.connection.fetchrow(query, *args)
        except asyncpg.PostgresError as e:
            logger.error("Error fetching row: %s", e)
            raise e
        except Exception as e:
            logger.error("Error fetching row: %s", e)
            raise e

    async def fetchval(self, query: str, *args: Any) -> Any:
        try:
            if not self.connection:
                await self.connect()
            return await self.connection.fetchval(query, *args)
        except asyncpg.PostgresError as e:
            logger.error("Error fetching value: %s", e)
            raise e

    async def insert_data(self, query: str, *args: Any, **kwargs: Any) -> str:
        return await self.execute(query, *args, **kwargs)
