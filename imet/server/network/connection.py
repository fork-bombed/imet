import websockets
from websockets.exceptions import WebSocketException
import imet
from imet.client.console import interface
from imet.server.network import actions
from IPython.core.interactiveshell import InteractiveShell


class WebSocketServer:
    def __init__(self, cli: interface.CLI, host: str = imet.HOST, port: int = imet.PORT, ping_interval=20, ping_timeout=10):
        self.host = host
        self.port = port
        self.server = None
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.clients = set()
        self.cli = cli
        self.ipython_shell = InteractiveShell.instance()

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

    async def handle_connection(self, websocket: websockets.WebSocketServerProtocol, path: str):
        self.clients.add(websocket)
        self.cli.output(f"New connection from {websocket.remote_address}")
        try:
            async for message in websocket:
                self.cli.output(f"Received message from {websocket.remote_address}: {message}")
                await actions.process_request(
                    websocket,
                    message,
                    self.cli,
                    self.ipython_shell
                )
        except WebSocketException as e:
            self.cli.error(f"Connection error: {e}")
        finally:
            self.clients.remove(websocket)
            self.cli.warn(f"Connection closed for {websocket.remote_address}")

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.cli.warn("Server stopped")
