import websockets
import msgpack
from imet.client.console import interface
from IPython.core.interactiveshell import InteractiveShell
import traceback
import io
import sys


async def process_request(websocket: websockets.WebSocketServerProtocol, data: bytes, cli: interface.CLI, ipython_shell: InteractiveShell):
    request = msgpack.unpackb(data, raw=False)
    if request.get("action") == "ipython":
        await handle_ipython(websocket, cli, request, ipython_shell)


async def handle_ipython(websocket: websockets.WebSocketServerProtocol, cli: interface.CLI, request: dict, ipython_shell: InteractiveShell):
    command = request.get("command")
    if command is not None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = stdout
        sys.stdin = stderr
        try:
            result = ipython_shell.run_cell(command)
            captured_stdout = stdout.getvalue()
            captured_stderr = stderr.getvalue()
            if result.success:
                output = None if result.result is None else str(result.result)
            else:
                tb_list = traceback.format_exception(
                    result.error_in_exec.__class__,
                    result.error_in_exec,
                    result.error_in_exec.__traceback__
                )
                output = "".join(tb_list)

            response = {
                "action": "ipython",
                "status": "ok" if result.success else "error",
                "output": output,
                "stdout": captured_stdout,
                "stderr": captured_stderr
            }
        except Exception as e:
            tb = traceback.format_exc()
            response = {
                "action": "ipython",
                "status": "error",
                "output": f"Exception: {str(e)}\n{tb}",
                "stdout": captured_stdout,
                "stderr": captured_stderr
            }
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
        packed_response = msgpack.packb(response)
        cli.output(f"Sending message: {str(packed_response)}")
        await websocket.send(packed_response)
