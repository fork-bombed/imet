from imet.client.console import interface
from imet.client.console.commands import imet_commands
from imet.client.console.commands.registry import CommandRegistry, IMETCommandException, IMETExit, process_command
import asyncio


async def main():
    console = interface.CLI()
    command_registry = CommandRegistry()
    imet_commands.register_commands(registry=command_registry, cli=console)

    console.output_banner()
    console.output("Type \"help\" or \"?\" to see a list of available commands")


    while True:
        user_input = await console.get_input()
        try:
            await process_command(
                command_registry=command_registry,
                command_str=user_input,
                cli=console
            )
        except IMETCommandException as e:
            console.error(e.message)
        except IMETExit as e:
            break

if __name__ == "__main__":
    asyncio.run(main())