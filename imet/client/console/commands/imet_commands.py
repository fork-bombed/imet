from imet.client.console.commands.registry import Command, CommandRegistry, IMETCommandException, IMETExit
from imet.client.console import interface


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
        )
    ]

    for command in commands:
        registry.register_command(command)