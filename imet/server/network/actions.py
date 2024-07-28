import websockets
import msgpack
from imet.client.console import interface


async def process_request(websocket: websockets.WebSocketServerProtocol, data: bytes, cli: interface.CLI):
    request = msgpack.unpackb(data, raw=False)
    cli.output(str(request))