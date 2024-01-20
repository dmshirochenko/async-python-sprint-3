import logging.config
from typing import Any, List, Dict
from datetime import datetime, timedelta

import asyncpg

from config.config import settings
from config.logger import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


class MessageLimitReachedError(Exception):
    pass


class MessageSender:
    def __init__(self, db_connector: asyncpg.Connection):
        self.db_connector = db_connector

    async def send_message(self, user_id: int, text: str) -> int:
        if not await self._can_send_message(user_id):
            raise MessageLimitReachedError("Message limit reached. Please wait until the limit is reset.")
        try:
            message_id = await self.insert_message(user_id, text)
        except asyncpg.PostgresError as e:
            logger.error("Error establishing database connection: %s", e)
            raise
        except Exception as e:
            logger.error("Error establishing database connection: %s", e)
        return message_id

    async def send_private_message(self, user_id: int, recipient_id: int, text: str) -> int:
        try:
            message_id = await self.insert_message(user_id, text)
            await self.insert_private_message(message_id, recipient_id)
        except asyncpg.PostgresError as e:
            logger.error("Error establishing database connection: %s", e)
            raise
        return message_id

    async def _can_send_message(self, user_id: int) -> bool:
        current_time = datetime.utcnow()
        try:
            message_limit = await self.db_connector.fetchrow(
                "SELECT message_count, reset_time FROM awesome_chat.message_limits WHERE user_id = $1", user_id
            )
        except asyncpg.PostgresError as e:
            logger.error("Error establishing database connection: %s", e)
            raise
        logger.info("Message limit is %s", message_limit)

        if not message_limit or message_limit["reset_time"] <= current_time:
            await self.db_connector.insert_data(
                "INSERT INTO awesome_chat.message_limits (user_id, message_count, reset_time) " "VALUES ($1, 1, $2) ",
                user_id,
                current_time + timedelta(hours=1),
            )
            return True

        elif message_limit["message_count"] < settings.max_messages_per_hour:
            await self.db_connector.execute(
                "UPDATE awesome_chat.message_limits SET message_count = message_count + 1 WHERE user_id = $1", user_id
            )
            return True

        else:
            return False

    async def insert_message(self, user_id: int, text: str) -> int:
        query = """
        INSERT INTO awesome_chat.messages (user_id, text, timestamp)
        VALUES ($1, $2, CURRENT_TIMESTAMP)
        RETURNING id
        """
        try:
            message_id = await self.db_connector.fetchval(query, user_id, text)
        except asyncpg.PostgresError as e:
            logger.error("Error establishing database connection: %s", e)
            raise
        return message_id

    async def insert_private_message(self, message_id: int, recipient_id: int) -> None:
        query = """
        INSERT INTO awesome_chat.private_messages (id, recipient_id)
        VALUES ($1, $2)
        """
        try:
            await self.db_connector.execute(query, message_id, recipient_id)
        except asyncpg.PostgresError as e:
            logger.error("Error establishing database connection: %s", e)
            raise

    async def retrieve_messages(self) -> List[Dict[str, Any]]:
        query = """
        SELECT m.user_id, m.text
        FROM awesome_chat.messages m
        LEFT JOIN awesome_chat.private_messages pm ON m.id = pm.id
        WHERE pm.id IS NULL
        ORDER BY m.timestamp DESC
        LIMIT 20
        """
        try:
            messages = await self.db_connector.fetch(query)
        except asyncpg.PostgresError as e:
            logger.error("Error establishing database connection: %s", e)
            raise
        return [dict(message) for message in messages]

    async def retrieve_private_messages(self, user_id: int, recipient_id: int) -> List[Dict[str, Any]]:
        query = """
        SELECT m.user_id, m.text
        FROM awesome_chat.messages m
        JOIN awesome_chat.private_messages pm ON m.id = pm.id
        WHERE (pm.recipient_id = $1 AND m.user_id = $2) OR (pm.recipient_id = $2 AND m.user_id = $1)
        ORDER BY m.timestamp DESC
        """
        try:
            private_messages = await self.db_connector.fetch(query, user_id, recipient_id)
        except asyncpg.PostgresError as e:
            logger.error("Error establishing database connection: %s", e)
            raise
        return [dict(message) for message in private_messages]

    async def is_user_exists(self, user_id: int) -> bool:
        exists = False
        query = "SELECT EXISTS(SELECT 1 FROM awesome_chat.users WHERE id = $1)"
        try:
            exists = await self.db_connector.fetchval(query, user_id)
            logger.info("Cheking is user %s exists, result %s ", user_id, exists)
        except Exception as e:
            logger.error("Error checking user existence: %s", e)
            raise
        return exists
