# get login for a particular user
# get login within a time period
# get logins for ip, user-agent, location
# get logins associated with alert type

from datetime import datetime
from typing import Annotated

import typer
from buffacli import config, requests
from buffacli.formatters import FormatOptions
from buffacli.models import LoginQuery

app = typer.Typer(help="Query login data.")


@app.command()
def logins(
    ctx: typer.Context,
    fields: Annotated[list[str], typer.Argument(help="Query fields to display")] = None,
    username: Annotated[str, typer.Option(help="Filter by username")] = None,
    ip: Annotated[str, typer.Option(help="Filter by IP address")] = None,
    index: Annotated[str, typer.Option(help="Filter by login index")] = None,
    country: Annotated[str, typer.Option(help="Filter by login country")] = None,
    login_start_time: Annotated[
        datetime, typer.Option(help="Filter by login date starting from date.")
    ] = None,
    login_end_time: Annotated[
        datetime, typer.Option(help="Filter by login date up to date.")
    ] = None,
    user_agent: Annotated[str, typer.Option(help="Filter by login agent.")] = None,
    omit: Annotated[
        list[str], typer.Option(help="Omit fields from query results")
    ] = None,
    mappings: Annotated[
        str,
        typer.Option(help="Alias name for fields. Follows the format fieldname:alias"),
    ] = None,
):
    if mappings:
        mappings = dict(mapstr.split(":") for mapstr in mappings.split())
    logins = requests.get_logins(
        username=username,
        ip=ip,
        country=country,
        login_start_time=login_start_time,
        login_end_time=login_end_time,
        user_agent=user_agent,
        index=index,
    )
    formatter = ctx.obj.formatter
    login = LoginQuery(
        logins[: ctx.obj.limit], omit=omit, fields=fields, mappings=mappings
    )
    formatter.print(login, title="Logins")
