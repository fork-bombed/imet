from typing import Callable
from imet.client.console import interface
import asyncio


class IMETCommandException(Exception):
    """Exception raised for errors related to IMET commands."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class IMETExit(Exception):
    """Exception raised for user-triggered exits."""
    def __init__(self):
        super().__init__()


class Command:
    def __init__(self, name: str, func: Callable, shortcuts: list[str]|None = None, description: str|None = None, usage: str|None = None, **kwargs):
        self.name = name
        self.func = func
        self.shortcuts = shortcuts or []
        self.description = description
        self.usage = usage
        self.func_args = kwargs


class CommandRegistry:
    def __init__(self):
        self.commands: dict[str, Command] = {}
        self.shortcuts: dict[str, str] = {}

    def register_command(self, command: Command):
        self.commands[command.name] = command
        for shortcut in command.shortcuts:
            if shortcut in self.shortcuts:
                raise IMETCommandException(f"Shortcut '{shortcut}' is already used for command '{self.shortcuts[shortcut]}'")
            self.shortcuts[shortcut] = command.name

    def find_command(self, name_or_shortcut: str) -> Command|None:
        command_name = self.shortcuts.get(name_or_shortcut, name_or_shortcut)
        return self.commands.get(command_name)
    

async def process_command(command_registry: CommandRegistry, command_str: str, cli: interface.CLI):
    parts = command_str.split()
    if not parts:
        return
    command_name = parts[0]
    command = command_registry.find_command(command_name)
    if command:
        try:
            if asyncio.iscoroutinefunction(command.func):
                await command.func(args=parts[1:], **command.func_args)
            else:
                command.func(args=parts[1:], **command.func_args)
        except IMETExit:
            raise
        except IMETCommandException:
            raise
        except Exception as e:
            raise IMETCommandException(f"Error executing command {command_name}: {e}")
    else:
        raise IMETCommandException(f"Unknown command {command_name}")