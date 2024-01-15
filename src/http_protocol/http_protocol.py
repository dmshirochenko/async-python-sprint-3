import asyncio
import h11


class HTTPProtocol(asyncio.Protocol):
    chat_history = []

    def __init__(self):
        self.connection = h11.Connection(h11.SERVER)

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

    async def handle_request(self):
        while True:
            event = await self.data_queue.get()
            if isinstance(event, h11.Request):
                if event.method.upper() == b"POST":
                    await self.handle_post(event)
                elif event.method.upper() == b"GET":
                    self.send_response(b"Chat History:\n" + b"\n".join(self.chat_history))
            elif isinstance(event, h11.ConnectionClosed):
                break

        if self.connection.our_state is h11.MUST_CLOSE:
            self.transport.close()

    async def handle_post(self, event):
        while True:
            event = await self.data_queue.get()
            if isinstance(event, h11.Data):
                message = event.data.decode("utf-8")
                if message == "test":
                    self.chat_history.append(event.data)
                break
            elif event is h11.EndOfMessage:
                return

        self.send_response(b"Message received and stored")

    def send_response(self, body):
        headers = [
            ("content-type", "text/plain"),
            ("content-length", str(len(body))),
        ]
        response = h11.Response(status_code=200, headers=headers)
        self.send(response)
        self.send(h11.Data(data=body))
        self.send(h11.EndOfMessage())

    def send(self, event):
        data = self.connection.send(event)
        self.transport.write(data)
