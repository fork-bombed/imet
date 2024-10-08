from imet.client.console.commands.registry import Command, CommandRegistry, IMETCommandException, IMETExit
from imet.client.console import interface
from IPython.terminal.embed import InteractiveShellEmbed
from IPython.core.completer import Completer, Completion
import imet
import asyncio
import nest_asyncio
import sys
import ast
import re
import os


nest_asyncio.apply()


class RemoteCompleter(Completer):
    def __init__(self, cli):
        super().__init__()
        self.cli = cli

    async def complete_request(self, text: str) -> list[str]:
        await self.cli.session.send({
            "action": "autocomplete",
            "text": text
        })
        response = await self.cli.session.receive()
        return response.get("matches", [])
        
    def completions(self, text, offset):
        try:
            last_non_alpha_index = len(text) - 1
            while last_non_alpha_index >= 0 and text[last_non_alpha_index].isalnum():
                last_non_alpha_index -= 1
            incomplete = text[last_non_alpha_index + 1:]
            completions = asyncio.run(self.complete_request(text))
            for match in completions:
                yield Completion(
                    text=match,
                    start=offset - len(incomplete),
                    end=offset
                )
        except Exception as e:
            self.cli.error(f"Completion error: {e}")


def help_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
    headers = ["command", "shortcuts", "usage", "description"]
    rows = []
    for command in registry.commands.values():
        shortcuts = ", ".join(command.shortcuts) if command.shortcuts else ""
        description = command.description or ""
        usage = command.usage or command.name
        rows.append([command.name, shortcuts, usage, description])
    cli.output_table(headers, rows)


async def exit_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
    if cli.session is not None and cli.session.is_connected():
        await cli.stop_session()
    cli.warn("Exiting IMET...")
    raise IMETExit()


async def connect_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
    if len(args) < 1:
        raise IMETCommandException("Connect requires a host argument e.g \"connect 127.0.0.1:1337\"")
    host = args[0]
    if not ":" in host:
        raise IMETCommandException(f"Please specify a port for the following host \"{host}\"")
    cli.output(f"Connecting to ws://{host}")
    await cli.new_session(host)
    if cli.session and cli.session.is_connected():
        cli.output(f"Session established successfully")


async def disconnect_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
    if cli.session is None or not cli.session.is_connected():
        raise IMETCommandException("No connected sessions found")
    await cli.stop_session()
    cli.warn("Session disconnected")


async def interactive_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
    if cli.session is None or not cli.session.is_connected():
        raise IMETCommandException("No connected sessions found")
    cli.output("Starting interactive IPython console...")

    async def execute_remote(shell, cli, code):
        if cli.session:
            try:
                await cli.session.send({
                    "action": "ipython",
                    "command": code
                })
                response = await cli.session.receive()
                if response is not None:
                    output = response.get("output")
                    stdout = response.get("stdout")
                    if output is not None:
                        if response.get("status") == "ok":
                            try:
                                evaluated_output = ast.literal_eval(output)
                            except (ValueError, SyntaxError):
                                evaluated_output = output
                            shell.displayhook(evaluated_output)
                            shell.history_manager.store_inputs(shell.execution_count, code)
                            shell.history_manager.store_output(evaluated_output)
                        else:
                            sys.stderr.write(stdout)
                            sys.stderr.flush()
                            shell.history_manager.store_inputs(shell.execution_count, code)
                    elif stdout:
                        sys.stdout.write(stdout)
                        sys.stdout.flush()
                        shell.history_manager.store_inputs(shell.execution_count, code)
                    shell.execution_count += 1
            except Exception as e:
                cli.error(f"Error: {e}")

    def custom_run_cell(shell, code):
        if code.strip() in ["exit()", "quit()", "exit", "quit"]:
            shell.ask_exit()
        elif not code.strip().startswith("%"):
            asyncio.run(execute_remote(shell, cli, code))
        else:
            shell.original_run_cell(code)

    try:
        shell = InteractiveShellEmbed()
        shell.execution_count = 0
        remote_completer = RemoteCompleter(cli)
        shell.Completer = remote_completer
        shell.original_run_cell = shell.run_cell
        shell.run_cell = lambda code, **kwargs: custom_run_cell(shell, code)
        shell.mainloop()
    except Exception as e:
        cli.error(f"Error in interactive session: {e}")
    finally:
        cli.warn("Exited interactive IPython console")


async def create_sample_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
    if len(args) < 1:
        raise IMETCommandException("Create requires a sample name e.g \"create malware_sample_1\"")
    
    sample_name = " ".join(args)
    valid_sample_name = sample_name.lower()
    valid_sample_name = valid_sample_name.replace(" ", "_").replace("-", "_")
    valid_sample_name = re.sub(r"[^a-z0-9_]", "", valid_sample_name)

    project_root = imet.get_project_root()
    samples_directory = os.path.join(project_root, "samples")
    script_filename = f"{valid_sample_name}.py"
    script_path = os.path.join(samples_directory, script_filename)

    if os.path.exists(script_path):
        override = await cli.prompt_yes_no(f"Sample \"{script_filename}\" already exists. Do you want to override it?")
        if not override:
            cli.warn("Sample creation cancelled")
            return

    template_directory = os.path.join(project_root, "server", "emulator")
    template_path = os.path.join(template_directory, "_template.py")

    with open(template_path) as f:
        template = f.read()

    description = await cli.prompt("Sample description: ")
    if description is None:
        return
    template = template.replace("{sample_name}", valid_sample_name).replace("{description}", description)
    
    with open(script_path, "w") as f:
        f.write(template)

    cli.output(f"Sample \"{valid_sample_name}\" written to {script_path}")


def extract_description_from_docstring(content: str) -> str:
    match = re.search(r'"""(.*?)"""', content, re.DOTALL)
    if match:
        docstring = match.group(1)
        description_match = re.search(r"Description:\s*(.*)", docstring)
        if description_match:
            return description_match.group(1).strip()
    return "N/A"


def get_samples_directory() -> str:
    project_root = imet.get_project_root()
    return os.path.join(project_root, "samples")


def find_samples() -> list[tuple[str, str]]:
    samples_directory = get_samples_directory()
    samples = []
    for filename in os.listdir(samples_directory):
        if filename.endswith(".py") and not filename.startswith("_"):
            file_path = os.path.join(samples_directory, filename)
            with open(file_path) as f:
                content = f.read()

            sample_name = filename.split(".py")[0]
            description = extract_description_from_docstring(content)
            samples.append((sample_name, description))
    return samples


async def samples_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
    if cli.session and cli.session.is_connected():
        cli.output("Searching for remote samples")
        await cli.session.send({
            "action": "samples",
            "search": args
        })
        response = await cli.session.receive()
        error = response.get("error")
        if error is not None:
            cli.error(error)
            return
        samples = response.get("samples", [])
        cli.output_table(["sample name", "description"], samples)
        return
    
    cli.output("Searching for local samples")
    samples = find_samples()

    if args:
        filtered_samples = []
        for sample_name, description in samples:
            if any(term.lower() in sample_name.lower() or term.lower() in description.lower() for term in args):
                filtered_samples.append((sample_name, description))
        samples = filtered_samples
    if samples:
        cli.output_table(["sample name", "description"], samples)
    else:
        matching_text = ""
        if args:
            args_joined = ", ".join(args)
            matching_text = f" matching term{'s' if len(args) > 1 else ''} {args_joined}"
        cli.error(f"No samples found{matching_text}")


async def emulate_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
    if len(args) < 1:
        raise IMETCommandException("Emulate requires a sample name e.g. \"emulate sample_name\"")
    
    sample_name = " ".join(args)
    
    if cli.session and cli.session.is_connected():
        cli.output(f"Sending emulation request for sample \"{sample_name}\"")
        await cli.session.send({
            "action": "emulate",
            "sample_name": sample_name
        })
        response = await cli.session.receive()
        message = response.get("message")
        error = response.get("error")
        if message:
            cli.output(message)
        if error:
            cli.error(error)
    else:
        raise IMETCommandException("No connected sessions found")
    

async def upload_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
    if len(args) < 1:
        raise IMETCommandException("Upload requires a sample name e.g \"upload sample_name\"")
    
    sample_name = " ".join(args).strip()
    samples_directory = get_samples_directory()
    local_file_path = os.path.join(samples_directory, f"{sample_name}.py")

    if not os.path.isfile(local_file_path):
        raise IMETCommandException(f"Local sample \"{sample_name}\" does not exist")

    with open(local_file_path) as f:
        script_content = f.read()

    if cli.session and cli.session.is_connected():
        cli.output(f"Uploading local sample \"{sample_name}\" to remote server")
        await cli.session.send({
            "action": "upload",
            "sample_name": sample_name,
            "script_content": script_content
        })
        response = await cli.session.receive()
        message = response.get("message")
        error = response.get("error")
        if message:
            cli.output(message)
        elif error:
            cli.error(error)
        else:
            cli.error("Unexpected error")
    else:
        cli.error("No connected sessions found")


def register_commands(registry: CommandRegistry, cli: interface.CLI):
    commands = [
        Command(
            name="help",
            shortcuts=["?"],
            description="Outputs all commands",
            func=help_command,
            cli=cli,
            registry=registry
        ),
        Command(
            name="exit",
            shortcuts=["quit", "q"],
            description="Exits IMET",
            func=exit_command,
            cli=cli,
            registry=registry
        ),
        Command(
            name="connect",
            shortcuts=["c", "conn"],
            description="Connect to server",
            usage="connect <host>",
            func=connect_command,
            cli=cli,
            registry=registry
        ),
        Command(
            name="disconnect",
            shortcuts=["d"],
            description="Disconnect from a server",
            usage="disconnect",
            func=disconnect_command,
            cli=cli,
            registry=registry
        ),
        Command(
            name="interactive",
            shortcuts=["i"],
            description="Open remote IPython console on the server",
            usage="interactive",
            func=interactive_command,
            cli=cli,
            registry=registry
        ),
        Command(
            name="create",
            shortcuts=["n", "new"],
            description="Create a new local sample script",
            usage="create <sample_name>",
            func=create_sample_command,
            cli=cli,
            registry=registry
        ),
        Command(
            name="samples",
            shortcuts=["list", "ls"],
            description="List all samples (filter by matching search term if provided)",
            usage="samples <terms?>",
            func=samples_command,
            cli=cli,
            registry=registry
        ),
        Command(
            name="emulate",
            shortcuts=["e", "em", "run"],
            description="Emulate a sample on the server",
            usage="emulate <sample_name>",
            func=emulate_command,
            cli=cli,
            registry=registry
        ),
        Command(
            name="upload",
            shortcuts=["u", "send"],
            description="Upload a local sample to the server",
            usage="upload <sample_name>",
            func=upload_command,
            cli=cli,
            registry=registry
        )
    ]

    for command in commands:
        registry.register_command(command)