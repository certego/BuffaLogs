from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from buffacli import export
from buffacli.commands.query import alerts, logins
from buffacli.formatters import FormatOptions
from buffacli.render import RenderOptions, make_renderable


@dataclass
class QueryOptions:
    limit: int | None = None
    formatter: FormatOptions = "table"


app = typer.Typer(help="Query users and alerts record")

app.add_typer(alerts.app, name="")
app.add_typer(logins.app, name="")


@app.callback()
def callback(
    ctx: typer.Context,
    formatter: Annotated[FormatOptions, typer.Option("-f", "--format")] = "table",
    limit: Annotated[int, typer.Option(help="Prints only the first n items")] = None,
    mode: Annotated[RenderOptions, typer.Option(help="Select how long output are displayed")] = "",
    page_size: Annotated[int, typer.Option(help="Number of items in a page")] = None,
    output_file: Annotated[Path, typer.Option("-o", "--output", help="Output file for query export")] = None,
    # search: Annotated[str, typer.Option(help="Performs post request search on key for the give value. Input should follow the format kw:value")] = None
):
    exporter = export.get_exporter(output_file)
    ctx.obj = QueryOptions(limit=limit, formatter=make_renderable(formatter, mode=mode, page_size=page_size, exporter=exporter))
