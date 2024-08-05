import importlib
import websockets
import msgpack
from imet.client.console import interface
from IPython.core.interactiveshell import InteractiveShell
from IPython.core.completer import provisionalcompleter
import traceback
import io
import sys
import re
import os
import imet


async def process_request(websocket: websockets.WebSocketServerProtocol, data: bytes, cli: interface.CLI, ipython_shell: InteractiveShell):
    request = msgpack.unpackb(data, raw=False)
    action = request.get("action")
    if action == "ipython":
        await handle_ipython(websocket, cli, request, ipython_shell)
    elif action == "autocomplete":
        await handle_autocomplete(websocket, cli, request, ipython_shell)
    elif action == "samples":
        await handle_samples_list(websocket, cli, request)
    elif action == "emulate":
        await handle_emulate(websocket, cli, request)


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


async def handle_autocomplete(websocket: websockets.WebSocketServerProtocol, cli: interface.CLI, request: dict, ipython_shell: InteractiveShell):
    text = request.get("text", "")
    try:
        completer = ipython_shell.Completer
        with provisionalcompleter():
            completions = list(completer.completions(text, len(text)))
        matches = [completion.text for completion in completions]
        response = {
            "action": "autocomplete",
            "matches": matches
        }
    except Exception as e:
        response = {
            "action": "autocomplete",
            "error": str(e),
            "matches": []
        }
    packed_response = msgpack.packb(response)
    cli.output(f"Sending autocomplete suggestions: {str(packed_response)}")
    await websocket.send(packed_response)


def extract_description_from_docstring(content: str) -> str:
    match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if match:
        docstring = match.group(1)
        description_match = re.search(r"Description:\s*(.*)", docstring)
        if description_match:
            return description_match.group(1).strip()
    return "N/A"


async def handle_samples_list(websocket: websockets.WebSocketServerProtocol, cli: interface.CLI, request: dict):
    samples = []
    project_root = imet.get_project_root()
    samples_directory = os.path.join(project_root, "samples")

    if not os.path.exists(samples_directory):
        cli.error(f"Samples directory not found: {samples_directory}")
        await websocket.send(msgpack.packb({
            "action": "samples",
            "error": "Samples directory not found"
        }))
        return

    for filename in os.listdir(samples_directory):
        if filename.endswith(".py") and not filename.startswith("_"):
            file_path = os.path.join(samples_directory, filename)
            with open(file_path) as f:
                content = f.read()

            sample_name = filename.split(".py")[0]
            description = extract_description_from_docstring(content)
            samples.append((sample_name, description))

    search_terms = request.get("search")
    if search_terms:
        filtered_samples = []
        for sample_name, description in samples:
            if any(term.lower() in sample_name.lower() or term.lower() in description.lower() for term in search_terms):
                filtered_samples.append((sample_name, description))
        samples = filtered_samples

    response = {
        "action": "samples",
        "samples": samples
    }
    if not samples:
        matching_text = ""
        if search_terms:
            args_joined = ", ".join(search_terms)
            matching_text = f" matching term{'s' if len(search_terms) > 1 else ''} {args_joined}"
        response = {
            "action": "samples",
            "error": f"No samples found{matching_text}"
        }
    await websocket.send(msgpack.packb(response))


async def handle_emulate(websocket: websockets.WebSocketServerProtocol, cli: interface.CLI, request: dict):
    sample_name = request.get("sample_name")
    if sample_name:
        _, sample_module = find_sample(sample_name)
        if sample_module is None:
            response = {
                "action": "emulate",
                "error": f"Sample \"{sample_name}\" does not exist"
            }
        else:
            try:
                if hasattr(sample_module, "emulate") and callable(sample_module.emulate):
                    cli.output(f"Running sample: {sample_name}")
                    sample_module.emulate()
                    response = {
                        "action": "emulate",
                        "message": f"Sample \"{sample_name}\" executed successfully"
                    }
                else:
                    response = {
                        "action": "emulate",
                        "error": f"The sample '{sample_name}' does not contain a valid 'emulate' function"
                    }
            except Exception as e:
                error_message = f"Error running sample \"{sample_name}\": {e}\n{traceback.format_exc()}"
                cli.error(error_message)
                response = {
                    "action": "emulate",
                    "error": error_message
                }
    else:
        response = {
                    "action": "emulate",
                    "error": "Sample name not provided"
                }

    await websocket.send(msgpack.packb(response))


def find_sample(sample_name: str) -> tuple[str, object|None]:
    valid_sample_name = sample_name.lower().replace(" ", "_").replace("-", "_")
    project_root = imet.get_project_root()
    samples_directory = os.path.join(project_root, "samples")
    sample_file = os.path.join(samples_directory, f"{valid_sample_name}.py")
    if not os.path.isfile(sample_file):
        return sample_file, None
    spec = importlib.util.spec_from_file_location(valid_sample_name, sample_file)
    sample_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sample_module)
    return sample_file, sample_module