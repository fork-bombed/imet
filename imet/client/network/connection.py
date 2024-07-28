import websockets
import asyncio
import msgpack
from websockets.exceptions import WebSocketException
import imet


class WebSocketClient:
    def __init__(self, uri: str, cli: "imet.client.console.interface.CLI"):
        self.uri = uri
        self.connection = None
        self.connected = False
        self.ping_task = None
        self.cli = cli

    def is_connected(self):
        return self.connected

    async def connect(self):
        try:
            self.connection = await websockets.connect(
                self.uri,
                ping_interval=20,
                ping_timeout=10
            )
            self.connected = True
            self.ping_task = asyncio.create_task(self.ping())
        except WebSocketException:
            await self.cli.stop_session()

    async def send(self, data: dict):
        if self.connected:
            packed_data = msgpack.packb(data)
            await self.connection.send(packed_data)

    async def receive(self) -> dict:
        if self.connected:
            data = await self.connection.recv()
            return msgpack.unpackb(data, raw=False)
        else:
            return None
        
    async def ping(self):
        while self.connected:
            try:
                await self.connection.ping()
                await asyncio.sleep(5)
            except websockets.ConnectionClosed:
                await self.cli.stop_session(connection_closed=True)
                break
            except asyncio.CancelledError:
                break
            except Exception:
                await self.cli.stop_session(connection_closed=True)
                break

    async def disconnect(self):
        if self.connection:
            await self.connection.close()
        self.connected = False
        if self.ping_task:
            self.ping_task.cancel()
        self.connection = None
