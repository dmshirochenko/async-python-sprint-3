from datetime import datetime, timedelta


class MessageSender:
    def __init__(self, db_connector):
        self.db_connector = db_connector

    async def send_message(self, user_id, text):
        if not await self._can_send_message(user_id):
            raise Exception("Message limit reached. Please wait until the limit is reset.")
        message_id = await self.insert_message(user_id, text)
        return message_id

    async def send_private_message(self, user_id, recipient_id, text):
        if not await self._can_send_message(user_id):
            raise Exception("Message limit reached. Please wait until the limit is reset.")
        message_id = await self.insert_message(user_id, text)
        await self.insert_private_message(message_id, recipient_id)
        return message_id

    async def _can_send_message(self, user_id):
        current_time = datetime.utcnow()
        message_limit = await self.db_connector.fetchrow(
            "SELECT message_count, reset_time FROM awesome_chat.message_limits WHERE user_id = $1", user_id
        )
        if not message_limit or message_limit["reset_time"] <= current_time:
            await self.db_connector.execute(
                "INSERT INTO awesome_chat.message_limits (user_id, message_count, reset_time) "
                "VALUES ($1, 1, $2) "
                "ON CONFLICT (user_id) DO UPDATE SET message_count = 1, reset_time = $2",
                user_id,
                current_time + timedelta(hours=1),
            )
            return True
        elif message_limit["message_count"] < 10:
            await self.db_connector.execute(
                "UPDATE awesome_chat.message_limits SET message_count = message_count + 1 WHERE user_id = $1", user_id
            )
            return True
        else:
            return False

    async def insert_message(self, user_id, text):
        query = """
        INSERT INTO awesome_chat.messages (user_id, text, timestamp)
        VALUES ($1, $2, CURRENT_TIMESTAMP)
        RETURNING id
        """
        message_id = await self.db_connector.fetchval(query, user_id, text)
        return message_id

    async def insert_private_message(self, message_id, recipient_id):
        query = """
        INSERT INTO awesome_chat.private_messages (id, recipient_id)
        VALUES ($1, $2)
        """
        recipient_id = int(recipient_id)
        await self.db_connector.execute(query, message_id, recipient_id)

    async def retrieve_messages(self):
        query = """
        SELECT m.user_id, m.text
        FROM awesome_chat.messages m
        LEFT JOIN awesome_chat.private_messages pm ON m.id = pm.id
        WHERE pm.id IS NULL
        ORDER BY m.timestamp DESC
        LIMIT 20
        """
        messages = await self.db_connector.fetch(query)
        return [dict(message) for message in messages]

    async def retrieve_private_messages(self, user_id, recipient_id):
        query = """
        SELECT m.user_id, m.text
        FROM awesome_chat.messages m
        JOIN awesome_chat.private_messages pm ON m.id = pm.id
        WHERE (pm.recipient_id = $1 AND m.user_id = $2) OR (pm.recipient_id = $2 AND m.user_id = $1)
        ORDER BY m.timestamp DESC
        """
        recipient_id = int(recipient_id)
        private_messages = await self.db_connector.fetch(query, user_id, recipient_id)
        return [dict(message) for message in private_messages]
