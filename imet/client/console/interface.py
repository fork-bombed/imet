from rich.console import Console
from rich.text import Text
from rich.table import Table
import imet
import pyfiglet


class CLI:
    def __init__(self, name: str = "imet"):
        self.name = name
        self.context = None
        self.console = Console()

    def set_context(self, context: str|None):
        self.context = context

    def set_no_context(self):
        self.set_context(None)

    def output_banner(self):
        ascii_art = pyfiglet.figlet_format(self.name, font="3d-ascii").rstrip()
        self.console.print(ascii_art, style="bold cyan")
        description_text = "\n[I]nteractive [M]alware [E]mulation [T]ool "
        description = Text(description_text, style="bold")
        letters_to_style = ['I', 'M', 'E', 'T']
        for letter in letters_to_style:
            start = description_text.find(f'[{letter}]')
            if start != -1:
                end = start + len(f'[{letter}]')
                description.stylize("cyan", start, end)
        version_text = f"({imet.VERSION})\n\n"
        description.append(version_text, style=None)
        self.console.print(description)

    def output(self, prompt: str):
        prompt_text = Text()
        prompt_text.append("[+] ", style="bold green")
        prompt_text.append(prompt)
        self.console.print(prompt_text)

    def error(self, prompt: str):
        prompt_text = Text()
        prompt_text.append("[-] ", style="bold red")
        prompt_text.append(prompt)
        self.console.print(prompt_text)

    def warn(self, prompt: str):
        prompt_text = Text()
        prompt_text.append("[!] ", style="bold yellow")
        prompt_text.append(prompt)
        self.console.print(prompt_text)

    def get_input(self) -> str:
        prompt_text = Text()
        prompt_text.append(self.name, style="underline bold")
        if self.context is not None:
            prompt_text.append(f" ({self.context})", style="bold red")
        prompt_text.append(" > ", style="bold")
        self.console.print(prompt_text, end="")
        return input()
    
    def output_table(self, headers: list[str], rows: list[list[str]]):
        table = Table(show_header=True, header_style="bold cyan", box=None)
        for header in headers:
            table.add_column(header, style="dim")
        for row in rows:
            table.add_row(*row)
        self.console.print(table)
