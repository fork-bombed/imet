from imet.client.console import interface
import asyncio
from imet.server.network.connection import WebSocketServer


console = interface.CLI()

console.output_banner()
console.output("Welcome to IMET server")

server = WebSocketServer(cli=console)

try:
    asyncio.run(server.start())
except KeyboardInterrupt:
    asyncio.run(server.stop())