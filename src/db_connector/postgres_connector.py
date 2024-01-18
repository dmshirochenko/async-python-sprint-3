import asyncpg

from src.backoff.backoff import retry_database_connection


class AsyncDatabaseConnector:
    def __init__(self, database_url):
        self.database_url = database_url
        self.connection = None

    async def _establish_connection(self):
        if self.connection is None or self.connection.is_closed():
            self.connection = await asyncpg.connect(self.database_url)

    @retry_database_connection()
    async def connect(self):
        self.connection = await asyncpg.connect(self.database_url)

    async def close(self):
        if self.connection:
            await self.connection.close()

    async def execute(self, query, *args, **kwargs):
        if not self.connection:
            await self.connect()
        if kwargs:
            return await self.connection.execute(query, *args, **kwargs)
        else:
            return await self.connection.execute(query, *args)

    async def fetch(self, query, *args):
        if not self.connection:
            await self.connect()
        return await self.connection.fetch(query, *args)

    async def fetchrow(self, query, *args):
        if not self.connection:
            await self.connect()
        return await self.connection.fetchrow(query, *args)

    async def fetchval(self, query, *args):
        if not self.connection:
            await self.connect()
        return await self.connection.fetchval(query, *args)

    async def insert_data(self, query, *args, **kwargs):
        return await self.execute(query, *args, **kwargs)
