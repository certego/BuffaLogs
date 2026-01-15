from datetime import datetime
from typing import Annotated

import typer
from buffacli import config, requests
from buffacli.formatters import FormatOptions
from buffacli.models import AlertQuery
from rich.console import Console

app = typer.Typer(help="Query alert data.")


@app.command()
def alerts(
    ctx: typer.Context,
    fields: Annotated[list[str], typer.Argument(help="Query fields to display")] = None,
    start_date: Annotated[
        datetime, typer.Option(help="Filter alerts from the date")
    ] = None,
    end_date: Annotated[datetime, typer.Option(help="Filter alerts up to date")] = None,
    name: Annotated[
        str, typer.Option("--alert-type", help="Filter by alert type")
    ] = None,
    username: Annotated[str, typer.Option(help="Filter by username")] = None,
    ip: Annotated[str, typer.Option(help="Filter by IP address")] = None,
    country: Annotated[str, typer.Option(help="Filter by login country code")] = None,
    is_vip: Annotated[
        bool, typer.Option("--is-vip", help="Filter by VIP status")
    ] = None,
    notified: Annotated[
        bool, typer.Option("--is-notified", help="Filter by notification status")
    ] = None,
    min_risk_score: Annotated[
        str, int, typer.Option(help="Exclude alerts below risk score")
    ] = None,
    max_risk_score: Annotated[
        str, int, typer.Option(help="Exclude alerts above risk score")
    ] = None,
    risk_score: Annotated[
        str, int, typer.Option(help="Include alerts with risk score")
    ] = None,
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
    alerts = requests.get_alerts(
        start_date=start_date,
        end_date=end_date,
        name=name,
        username=username,
        ip=ip,
        country=country,
        is_vip=is_vip,
        notified=notified,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
        risk_score=risk_score,
        login_start_time=login_start_time,
        login_end_time=login_end_time,
        user_agent=user_agent,
    )
    formatter = ctx.obj.formatter
    alert_model = AlertQuery(
        alerts[: ctx.obj.limit], omit=omit, fields=fields, mappings=mappings
    )
    formatter.print(alert_model, title="Alerts")
