import json
import urllib.parse
import logging.config

import h11
import asyncio

from config.config import settings
from config.logger import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


class HTTPProtocol(asyncio.Protocol):
    def __init__(self, auth_instance, message_sender_instance):
        self.connection = h11.Connection(h11.SERVER)
        self.auth_instance = auth_instance
        self.message_sender_instance = message_sender_instance
        self.request_buffer = bytearray()
        self.current_request = None

    def connection_made(self, transport):
        self.transport = transport
        logger.info("New connection has been made ...")

    def data_received(self, data):
        self.connection.receive_data(data)
        while True:
            event = self.connection.next_event()
            logger.info("Event to handle %s", event)
            if event is h11.NEED_DATA:
                break

            if isinstance(event, h11.Request):
                self.current_request = event
                self.request_buffer.clear()

            elif isinstance(event, h11.Data):
                logger.info("Received data new %s", event.data)
                self.request_buffer.extend(event.data)

            elif isinstance(event, h11.EndOfMessage):
                logger.info("Request buffer sent to event loop %s", self.request_buffer)
                request_copy = self.current_request
                buffer_copy = self.request_buffer.copy()
                asyncio.create_task(self.handle_request(request_copy, buffer_copy))
                self.current_request = None
                self.request_buffer.clear()

            elif isinstance(event, h11.ConnectionClosed):
                # Handling the connection close event
                if self.connection.our_state is h11.MUST_CLOSE:
                    self.transport.close()

    def _extract_token(self, headers):
        for name, value in headers:
            if name.lower() == b"authorization":
                return value.decode("utf-8")
        return None

    async def handle_request(self, request_headers, request_body):
        logger.info("Proceeding with headers %s  and body  %s", request_headers, request_body)
        parsed_target = urllib.parse.urlparse(request_headers.target.decode("utf-8"))
        method = request_headers.method.upper()

        try:
            if method == b"GET":
                await asyncio.wait_for(
                    self.handle_get_request(parsed_target, request_headers, request_body),
                    timeout=settings.max_request_time,
                )
            elif method == b"POST":
                await asyncio.wait_for(
                    self.handle_post_request(parsed_target, request_headers, request_body),
                    timeout=settings.max_request_time,
                )
        except asyncio.TimeoutError:
            logger.error("Request processing timed out")
            self.send_timeout_response()

    async def handle_get_request(self, parsed_target, request_headers, request_body):
        if parsed_target.path == "/status":
            token = self._extract_token(request_headers.headers)
            await self.handle_status(parsed_target, token)
        elif parsed_target.path == "/health":
            await self.handle_health()

    async def handle_post_request(self, parsed_target, request_headers, request_body):
        token = self._extract_token(request_headers.headers)
        if parsed_target.path == "/connect":
            await self.handle_connect()
        elif parsed_target.path == "/send":
            await self.handle_send(request_body, token)
        elif parsed_target.path == "/send-private":
            await self.handle_send(request_body, token, message_type="private")

    async def handle_health(self):
        try:
            response = {"status": "OK"}
            response_info = json.dumps(response).encode()
            self.send_response(response_info)
        except Exception as e:
            logger.error(f"Error in handle_health: {e}")
            self.send_error_response(settings.error_messages.internal_server_error)

    async def handle_connect(self):
        try:
            logger.info("User auth starting ...")
            token = await self.auth_instance.create_user_and_token()

            if token is not None:
                user_id = await self.auth_instance.get_user_id_from_token(token)
                if user_id is not None:
                    response = {"status": "success", "user_id": user_id}
                    connection_info = json.dumps(response).encode()
                    self.send_response(connection_info, token)
                else:
                    self.send_error_response(settings.error_messages.unauthorized)
            else:
                self.send_error_response(settings.error_messages.internal_server_error)
        except Exception as e:
            logger.error(f"Error in handle_connect: {e}")
            self.send_error_response(settings.error_messages.internal_server_error)

    def _parse_query_params(self, parsed_url):
        query_params = urllib.parse.parse_qs(parsed_url.query)
        return {k: v[0] for k, v in query_params.items()}

    async def handle_status(self, parsed_target, token=None):
        try:
            query_params = self._parse_query_params(parsed_target)
            chat_type = query_params.get("chat_type")
            recipient_id = query_params.get("recipient_id")

            if not token:
                self.send_error_response(settings.error_messages.unauthorized)
                return

            user_id = await self.auth_instance.get_user_id_from_token(token)
            if user_id is None:
                self.send_error_response(settings.error_messages.unauthorized)
                return

            if chat_type == "common":
                all_messages = await self.message_sender_instance.retrieve_messages()
                response = {"messages": all_messages}
            elif chat_type == "private" and recipient_id:
                private_messages = await self.message_sender_instance.retrieve_private_messages(user_id, recipient_id)
                response = {"messages": private_messages}
            else:
                self.send_error_response(settings.error_messages.invalid_parameters)
                return

            status_info = json.dumps(response).encode()
            self.send_response(status_info)

        except Exception as e:
            logger.error(f"Error in handle_status: {e}")
            self.send_error_response(settings.error_messages.internal_server_error)

    async def handle_send(self, request_body, token, message_type=None):
        try:
            logger.info("Received data %s", request_body)
            user_id = await self.auth_instance.get_user_id_from_token(token)

            message_data = json.loads(request_body.decode("utf-8"))
            text = message_data["text"]
            recipient_id = message_data.get("recipient_id")

            message_id = await self.message_sender_instance.insert_message(user_id, text)
            if message_type == "private" and recipient_id is not None:
                await self.message_sender_instance.insert_private_message(message_id, recipient_id)

            response_body = json.dumps({"message": "Message received."}).encode("utf-8")
            self.send_response(response_body)
        except json.JSONDecodeError:
            self.send_error_response(settings.error_messages.invalid_json_format)
        except KeyError:
            self.send_error_response(settings.error_messages.missing_required_data)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.send_error_response(settings.error_messages.internal_server_error)

    def send_response(self, body, token=None):
        headers = [
            ("Content-Type", "application/json"),
            ("content-length", str(len(body))),
        ]
        if token:
            headers.append((("Authorization", str(token))))
        response = h11.Response(status_code=200, headers=headers)
        self.send(response)
        self.send(h11.Data(data=body))
        self.send(h11.EndOfMessage())

    def send_timeout_response(self):
        timeout_response = json.dumps({"error": "Request processing timed out"}).encode("utf-8")
        self.send_response(timeout_response, status_code=408)

    def send_error_response(self, error):
        response_body = json.dumps({"error": error.message}).encode("utf-8")
        headers = [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(response_body))),
        ]
        response = h11.Response(status_code=error.status_code, headers=headers)
        self.send(response)
        self.send(h11.Data(data=response_body))
        self.send(h11.EndOfMessage())

    def send(self, event):
        data = self.connection.send(event)
        self.transport.write(data)
