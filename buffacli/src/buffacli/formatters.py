import functools
import inspect
import json
import re
from enum import Enum
from typing import Any

from buffacli.globals import vprint
from buffacli.models import DataModel
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Column, Table
from rich.text import Text


def print_func(formatter: callable):
    sig = inspect.signature(formatter)

    @functools.wraps(formatter)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        console = Console()
        if not console.is_terminal:
            # print raw response content
            content = bound.arguments["content"]
            print(content.raw)
        else:
            console.print(formatter(*args, **kwargs))

    return wrapper


def as_table(content: DataModel, title: str):
    """
    Prints out a table representation of content.

    Args:
        content [DataModel]: Must implement the `.table` property

    Expected format (of `.table` return value):
        {
            'header_1'  : [row_1, row_2, row_3],
            'header_2' : [row_1, row_2, row_3]
        }
    """
    vprint("debug", "Formating as table...")
    headers = content.table.keys()
    columns = [Column(header, justify="left") for header in headers]
    table = Table(*columns, show_header=True, header_style="bold cyan", title=title)
    rows = zip(*content.table.values())
    for row in rows:
        table.add_row(*[str(item) for item in row])  # Rich Table cannot render int
    return table


def as_json(content: DataModel, title: str):
    """
    Prints out the raw JSON representation of the API response.

    Args:
        content [DataModel] : Must implement the `.json` property
        title : str

    Expected Format (of `.json` return value) : Any valid dictionary object
    """
    vprint("debug", "Formating as JSON...")
    json_format = json.dumps(content.json, indent=2)
    json_format = json_format[1:-1]
    json_output = re.sub(r'(".*?":)', r"[bold cyan]\1[/bold cyan]", json_format)
    panel = Panel(json_output, title=title, expand=True)
    return panel


class FormatOptions(str, Enum):
    def __new__(cls, value: str, formatter: callable):
        obj = str.__new__(cls)
        obj._value_ = value
        obj.formatter = formatter
        obj.print = print_func(formatter)
        return obj

    table = "table", as_table
    json = "json", as_json
