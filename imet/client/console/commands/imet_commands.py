from imet.client.console.commands.registry import Command, CommandRegistry, IMETExit
from imet.client.console import interface


def help_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
    headers = ["command", "shortcuts", "description"]
    rows = []
    for command in registry.commands.values():
        shortcuts = ", ".join(command.shortcuts) if command.shortcuts else ""
        description = command.description or ""
        rows.append([command.name, shortcuts, description])
    cli.output_table(headers, rows)


def exit_command(cli: interface.CLI, args: list[str], registry: CommandRegistry):
    cli.warn("Exiting IMET...")
    raise IMETExit()


def register_commands(registry: CommandRegistry, cli: interface.CLI):
    registry.register_command(
        Command(
            name="help",
            shortcuts=["?"],
            description="Outputs all commands",
            func=help_command,
            cli=cli,
            registry=registry
        )
    )
    registry.register_command(
        Command(
            name="exit",
            shortcuts=["quit"],
            description="Exits IMET",
            func=exit_command,
            cli=cli,
            registry=registry
        )
    )