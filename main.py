import asyncio
import os
from dotenv import load_dotenv

from src.auth.auth_simple import Auth
from src.http_protocol.http_protocol import HTTPProtocol
from src.db_connector.postgres_connector import AsyncDatabaseConnector
from src.message_sender.message_sender import MessageSender

# Load environment variables from .env file
load_dotenv()


async def main(host, port):
    loop = asyncio.get_running_loop()

    # Use environment variable for database URL
    db_url = os.getenv("DATABASE_URL", "postgresql://app_test:123test@postgres/db_awesome_chat")

    db_connector = AsyncDatabaseConnector(db_url)
    await db_connector.connect()
    auth_instance = Auth(db_connector)
    message_sender_instance = MessageSender(db_connector)

    def protocol_factory():
        return HTTPProtocol(auth_instance=auth_instance, message_sender_instance=message_sender_instance)

    server = await loop.create_server(protocol_factory, host, port)
    await server.serve_forever()


asyncio.run(main("0.0.0.0", 8000))
