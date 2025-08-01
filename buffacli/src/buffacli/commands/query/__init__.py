from dataclasses import dataclass
from enum import Enum
from typing import Annotated

import typer
from buffacli.commands.query import alerts, users
from buffacli.formatters import FormatOptions
from buffacli.render import make_renderable


@dataclass
class QueryOptions:
    limit: int | None = None
    search: str | None = None
    less: bool | None = None
    formatter: FormatOptions = "table"


class DisplayMode(str, Enum):
    less = "less"
    shell = "shell"
    paginate = "paginate"
    default = ""


app = typer.Typer(help="Query users and alerts record")

app.add_typer(alerts.app, name="")


@app.callback()
def callback(
    ctx: typer.Context,
    formatter: Annotated[FormatOptions, typer.Option("-f", "--format")] = "table",
    limit: Annotated[int, typer.Option(help="Prints only the first n items")] = None,
    mode: Annotated[DisplayMode, typer.Option(help="Select how long output are displayed")] = "",
    page_size: Annotated[int, typer.Option(help="Number of items in a page")] = None,
    # search: Annotated[str, typer.Option(help="Performs post request search on key for the give value. Input should follow the format kw:value")] = None
):

    ctx.obj = QueryOptions(limit=limit, formatter=make_renderable(formatter, mode=mode, page_size=page_size))  # , search=search),
