from imet.client.console import interface
import asyncio
from imet.server.network.connection import WebSocketServer
from IPython.core.interactiveshell import InteractiveShell


async def setup_ipython_shell():
    ipython_shell = InteractiveShell.instance()
    await ipython_shell.run_code("from imet.server.api import imetapi, winapi, payloads")
    return ipython_shell


console = interface.CLI()

console.output_banner()
console.output("Welcome to IMET server")

shell = asyncio.run(setup_ipython_shell())
server = WebSocketServer(cli=console, ipython_shell=shell)

try:
    asyncio.run(server.start())
except KeyboardInterrupt:
    asyncio.run(server.stop())