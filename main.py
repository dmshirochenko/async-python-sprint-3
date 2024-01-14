import asyncio

from src.http_protocol import HTTPProtocol


async def main(host, port):
    loop = asyncio.get_running_loop()
    server = await loop.create_server(HTTPProtocol, host, port)
    await server.serve_forever()


asyncio.run(main("127.0.0.1", 8000))
