import secrets
from typing import Optional

import asyncio

from src.db_connector.postgres_connector import AsyncDatabaseConnector


class Auth:
    def __init__(self, db: AsyncDatabaseConnector):
        self.db = db

    async def create_user_and_token(self, username: Optional[str] = None) -> Optional[str]:
        try:
            if not username:
                random_part1 = secrets.token_hex(4)
                random_part2 = secrets.token_hex(4)
                username = f"awesome_{random_part1}_user_{random_part2}"

            # SQL query to insert a new user
            user_insert_query = """
            INSERT INTO awesome_chat.users (username)
            VALUES ($1)
            RETURNING id
            """
            user_id = await self.db.fetchval(user_insert_query, username)

            token = secrets.token_urlsafe()
            session_insert_query = """
            INSERT INTO awesome_chat.user_sessions (user_id, session_token)
            VALUES ($1, $2)
            """
            await self.db.execute(session_insert_query, user_id, token)

            return token
        except Exception as e:
            print(f"Error creating user and token: {e}")
            return None

    async def get_user_id_from_token(self, token: str) -> Optional[int]:
        try:
            session_select_query = """
            SELECT user_id
            FROM awesome_chat.user_sessions
            WHERE session_token = $1 AND is_active = True
            """
            session = await self.db.fetchrow(session_select_query, token)
            if session:
                return session["user_id"]
            else:
                raise ValueError("Invalid or inactive token")
        except Exception as e:
            print(f"Error retrieving user ID from token: {e}")
            return None


if __name__ == "__main__":

    async def run():
        db_url = "postgresql://app_test:123test@localhost/db_awesome_chat"
        db = AsyncDatabaseConnector(db_url)
        await db.connect()
        auth = Auth(db)

        try:
            token = await auth.create_user_and_token()
            if token:
                user_id = await auth.get_user_id_from_token(token)
                print(user_id)
        finally:
            await db.close()

    asyncio.run(run())
