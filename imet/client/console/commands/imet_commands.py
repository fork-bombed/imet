from imet.client.console.commands.registry import Command, CommandRegistry, IMETCommandException, IMETExit
from imet.client.console import interface
from IPython.terminal.embed import InteractiveShellEmbed
import asyncio
import nest_asyncio
import sys
import ast


nest_asyncio.apply()


def help_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
    headers = ["command", "shortcuts", "usage", "description"]
    rows = []
    for command in registry.commands.values():
        shortcuts = ", ".join(command.shortcuts) if command.shortcuts else ""
        description = command.description or ""
        usage = command.usage or command.name
        rows.append([command.name, shortcuts, usage, description])
    cli.output_table(headers, rows)


def exit_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
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
    

async def send_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
    if cli.session is None or not cli.session.is_connected():
        raise IMETCommandException("No connected sessions found")
    if len(args) < 1:
        raise IMETCommandException("No args")
    await cli.session.send(" ".join(args))
    response = await cli.session.receive()
    cli.output(f"Response from server: {response}")


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
                shell.execution_count += 1
                if response is not None:
                    output = response.get("output")
                    if output is not None:
                        if response.get("status") == "ok":
                            try:
                                evaluated_output = ast.literal_eval(output)
                            except (ValueError, SyntaxError):
                                evaluated_output = output
                            shell.displayhook(evaluated_output)
                        else:
                            sys.stderr.write(f"{output}\n")
                            sys.stderr.flush()
            except Exception as e:
                print(f"Error: {e}")

    def custom_run_cell(shell, code):
        if not code.strip().startswith("%"):
            asyncio.run(execute_remote(shell, cli, code))
        else:
            shell.original_run_cell(code)

    try:
        shell = InteractiveShellEmbed()
        shell.execution_count = 0
        shell.original_run_cell = shell.run_cell
        shell.run_cell = lambda code, **kwargs: custom_run_cell(shell, code)
        shell.mainloop()
    except Exception as e:
        cli.error(f"Error in interactive session: {e}")
    finally:
        cli.warn("Exited interactive IPython console")



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
            name="send",
            shortcuts=["s"],
            description="Send a message to server",
            usage="send <message>",
            func=send_command,
            cli=cli,
            registry=registry
        ),
        Command(
            name="interactive",
            shortcuts=["i"],
            description="Open remove IPython console on the server",
            usage="interactive",
            func=interactive_command,
            cli=cli,
            registry=registry
        )
    ]

    for command in commands:
        registry.register_command(command)