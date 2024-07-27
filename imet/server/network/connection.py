import asyncio
import websockets
from websockets.exceptions import WebSocketException
import imet
from imet.client.console import interface


class WebSocketServer:
    def __init__(self, host=imet.HOST, port=imet.PORT, cli=interface.CLI, ping_interval=20, ping_timeout=10):
        self.host = host
        self.port = port
        self.server = None
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.clients = set()
        self.cli = cli

    async def start(self):
        self.server = await websockets.serve(
            self.handle_connection, 
            self.host, 
            self.port,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout
        )
        self.cli.output(f"Server started and listening on {self.host}:{self.port}")
        await self.server.wait_closed()

    async def handle_connection(self, websocket, path):
        # Add the new client to the set of connected clients
        self.clients.add(websocket)
        self.cli.output(f"New connection from {websocket.remote_address}")
        try:
            async for message in websocket:
                self.cli.output(f"Received message from {websocket.remote_address}: {message}")
                # Handle incoming message (e.g., broadcast to all clients)
                await self.handle_message(websocket, message)
        except WebSocketException as e:
            self.cli.error(f"Connection error: {e}")
        finally:
            self.clients.remove(websocket)
            self.cli.warn(f"Connection closed for {websocket.remote_address}")

    async def handle_message(self, websocket, message):
        await websocket.send(f"Echo: {message}")

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.cli.warn("Server stopped.")
