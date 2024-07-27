from imet.client.console import interface
from imet.client.console.commands import imet_commands
from imet.client.console.commands.registry import CommandRegistry, IMETCommandException, IMETExit, process_command


console = interface.CLI()
command_registry = CommandRegistry()
imet_commands.register_commands(registry=command_registry, cli=console)

console.output_banner()
console.output("Type \"help\" or \"?\" to see a list of available commands")


while True:
    user_input = console.get_input()
    try:
        process_command(
            command_registry=command_registry,
            command_str=user_input,
            cli=console
        )
    except IMETCommandException as e:
        console.error(e.message)
    except IMETExit as e:
        break