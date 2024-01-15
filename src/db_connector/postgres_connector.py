import asyncpg


class AsyncDatabaseConnector:
    def __init__(self, database_url):
        self.database_url = database_url
        self.connection = None

    async def connect(self):
        self.connection = await asyncpg.connect(self.database_url)

    async def close(self):
        if self.connection:
            await self.connection.close()

    async def execute(self, query, *args):
        if not self.connection:
            await self.connect()
        return await self.connection.execute(query, *args)

    async def fetch(self, query, *args):
        if not self.connection:
            await self.connect()
        return await self.connection.fetch(query, *args)

    async def fetchrow(self, query, *args):
        if not self.connection:
            await self.connect()
        return await self.connection.fetchrow(query, *args)

    async def fetch_data(self, query):
        return await self.fetch(query)

    async def insert_data(self, query, *args):
        return await self.execute(query, *args)
