import asyncio
import h11
import json
import urllib.parse
import json


class HTTPProtocol(asyncio.Protocol):
    chat_history = []

    def __init__(self, auth_instance, message_sender_instance):
        self.connection = h11.Connection(h11.SERVER)
        self.auth_instance = auth_instance
        self.message_sender_instance = message_sender_instance

    def connection_made(self, transport):
        self.transport = transport
        self.data_queue = asyncio.Queue()
        asyncio.create_task(self.handle_request())

    def data_received(self, data):
        self.connection.receive_data(data)
        asyncio.create_task(self.process_data())

    async def process_data(self):
        while True:
            event = self.connection.next_event()
            if event is h11.NEED_DATA:
                break
            await self.data_queue.put(event)

    def _extract_token(self, headers):
        for name, value in headers:
            if name.lower() == b"authorization":
                return value.decode("utf-8")
        return None

    async def handle_request(self):
        while True:
            event = await self.data_queue.get()
            if isinstance(event, h11.Request):
                token = self._extract_token(event.headers)
                parsed_target = urllib.parse.urlparse(event.target.decode("utf-8"))
                print(parsed_target)
                if event.method.upper() == b"POST" and parsed_target.path == "/connect":
                    await self.handle_connect(event)
                elif event.method.upper() == b"GET" and parsed_target.path == "/status":
                    await self.handle_status(event, token)
                elif event.method.upper() == b"GET" and parsed_target.path == "/health":
                    await self.handle_health(event)
                elif event.method.upper() == b"POST" and parsed_target.path == "/send":
                    await self.handle_send(event, token)
                elif event.method.upper() == b"POST" and parsed_target.path == "/send-private":
                    await self.handle_send(event, token, message_type="private")
            elif isinstance(event, h11.ConnectionClosed):
                break

        if self.connection.our_state is h11.MUST_CLOSE:
            self.transport.close()

    async def handle_health(self, event):
        response = {"status": "OK"}
        response_info = json.dumps(response).encode()
        await self.send_response(response_info)

    async def handle_connect(self, event):
        response = {"status": "failure", "user_id": None}
        token = await self.auth_instance.create_user_and_token()

        if token:
            user_id = await self.auth_instance.get_user_id_from_token(token)
            if user_id is not None:
                response["status"] = "success"
                response["user_id"] = user_id

        # Assuming you still need to send some response back
        connection_info = json.dumps(response).encode()
        self.send_response(connection_info, token)

        return response

    def _parse_query_params(self, url):
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        return {k: v[0] for k, v in query_params.items()}

    async def handle_status(self, event, token=None):
        # Extract chat_type and user_name from event
        query_params = self._parse_query_params(event.target.decode("utf-8"))
        print(query_params)
        chat_type = query_params.get("chat_type")
        recipient_id = query_params.get("recipient_id")
        user_id = await self.auth_instance.get_user_id_from_token(token)
        print(chat_type, user_id, recipient_id)
        if chat_type == "common":
            all_messages = await self.message_sender_instance.retrieve_messages()
            response = {"messages": all_messages}
        elif chat_type == "private" and recipient_id:
            private_messages = await self.message_sender_instance.retrieve_private_messages(user_id, recipient_id)
            response = {"messages": private_messages}
        else:
            response = {"message": "Invalid parameters"}
        print(response)
        status_info = json.dumps(response).encode()
        self.send_response(status_info)

    async def handle_send(self, event, token, message_type=None):
        while True:
            event = await self.data_queue.get()
            if isinstance(event, h11.Data):
                user_id = await self.auth_instance.get_user_id_from_token(token)

                try:
                    message_data = json.loads(event.data.decode("utf-8"))
                    print("message_data", message_data)
                    text = message_data["text"]
                    recipient_id = message_data.get("recipient_id")
                except (json.JSONDecodeError, KeyError):
                    self.send_response(b"Invalid message format")
                    break

                message_id = await self.message_sender_instance.insert_message(user_id, text)
                if message_type == "private" and recipient_id is not None:
                    await self.message_sender_instance.insert_private_message(message_id, recipient_id)

                break
            elif event is h11.EndOfMessage:
                return

        self.send_response(b"Message received.")

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

    def send(self, event):
        data = self.connection.send(event)
        self.transport.write(data)
