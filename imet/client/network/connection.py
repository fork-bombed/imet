import websockets
import asyncio
from websockets.exceptions import WebSocketException


class WebSocketClient:
    def __init__(self, uri: str):
        self.uri = uri
        self.connection = None
        self.connected = False
        self.ping_task = None

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
            self.connected = False

    async def send(self, message: str):
        if self.connected:
            await self.connection.send(message)

    async def receive(self):
        if self.connected:
            return await self.connection.recv()
        else:
            return None
        
    async def ping(self):
        while self.connected:
            try:
                await self.connection.ping()
                await asyncio.sleep(5)
            except websockets.ConnectionClosed:
                self.connected = False
                raise
            except asyncio.CancelledError:
                break
            except Exception:
                break

    async def disconnect(self):
        if self.connection:
            await self.connection.close()
            self.connected = False
            self.ping_task.cancel()
            await self.ping_task
            self.ping_task = None
