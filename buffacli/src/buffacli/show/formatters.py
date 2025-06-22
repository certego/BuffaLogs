import json
import re
from enum import Enum

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Column, Table
from rich.text import Text


def as_table(content: list[dict], headers: list[str], title: str):
    columns = [Column(header, justify="left") for header in headers]
    table = Table(*columns, show_header=True, header_style="bold cyan", title=title)
    for row in content:
        table.add_row(*[row[header] for header in headers])
    console = Console()
    console.print(table)


def as_json(content: list[dict], headers: list[str], title: str):
    json_format = json.dumps(content, indent=2)
    json_output = re.sub(r'(".*?":)', r"[bold cyan]\1[/bold cyan]", json_format)
    key_note = Text(f"keys: {', '.join(headers)}", style="bold cyan")
    panel = Panel(json_output, title=title, expand=False, subtitle=key_note)
    console = Console()
    console.print(panel)


def as_markdown(content: list[dict], headers: list[str], title: str):
    markdown_content = f"## {title}\n"
    body = []
    for row in content:
        body.append("\n".join(f"* **{header}** : {row[header]}" for header in headers))

    markdown_content += "\n---\n".join(body)
    markdown_output = Markdown(markdown_content)
    panel = Panel(markdown_output, title=title, expand=False)
    console = Console()
    console.print(panel)


class FormatOptions(str, Enum):

    def __new__(cls, value: str, formatter: callable):
        obj = str.__new__(cls)
        obj._value_ = value
        obj.formatter = formatter
        return obj

    table = "table", as_table
    json = "json", as_json
    markdown = "markdown", as_markdown
