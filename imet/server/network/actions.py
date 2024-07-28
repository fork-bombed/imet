import websockets
import msgpack
from imet.client.console import interface
from IPython.core.interactiveshell import InteractiveShell
import traceback


async def process_request(websocket: websockets.WebSocketServerProtocol, data: bytes, cli: interface.CLI, ipython_shell: InteractiveShell):
    request = msgpack.unpackb(data, raw=False)
    if request.get("action") == "ipython":
        await handle_ipython(websocket, cli, request, ipython_shell)


async def handle_ipython(websocket: websockets.WebSocketServerProtocol, cli: interface.CLI, request: dict, ipython_shell: InteractiveShell):
    command = request.get("command")
    if command is not None:
        try:
            result = ipython_shell.run_cell(command)
            print(result, result.success)
            if result.success:
                output = str(result.result)
            else:
                # Generate a detailed traceback
                tb_list = traceback.format_exception(
                    result.error_in_exec.__class__,
                    result.error_in_exec,
                    result.error_in_exec.__traceback__
                )
                output = ''.join(tb_list)

            response = {
                "action": "ipython",
                "status": "ok" if result.success else "error",
                "output": output
            }
        except Exception as e:
            tb = traceback.format_exc()
            response = {
                "action": "ipython",
                "status": "error",
                "output": f"Exception: {str(e)}\n{tb}"
            }
        packed_response = msgpack.packb(response)
        cli.output(f"Sending message: {str(packed_response)}")
        await websocket.send(packed_response)
