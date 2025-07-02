from typing import Annotated

import typer
from buffacli import config, requests
from buffacli.formatters import FormatOptions
from buffacli.models import AlertType, Ingestion

help_text = (
    "This command group provides visibility into BuffaLogs'"
    "available configurations, such as supported alerters,"
    "ingestors and configuration schema.\n"
    "Useful for inspecting system capabilities or"
    "integrating BuffaLogs with external tools."
)


app = typer.Typer(help=help_text)


@app.command()
def alert_types(
    format_option: Annotated[FormatOptions, typer.Option("--format", "-f", help="specify display format")] = "table",
    include_description: Annotated[bool, typer.Option(help="Include alert types description.")] = False,
):
    """Display supported alert types."""
    content = requests.get_alert_types()
    alert_types = AlertType(content, include_description)
    format_option.print(alert_types, title="Supported Alert Types")


@app.command()
def ingestion(
    format_option: Annotated[FormatOptions, typer.Option("--format", "-f", help="specify display format")] = "table",
    active_ingestion: Annotated[bool, typer.Option("--active", help="Print active ingestion source")] = False,
    source: Annotated[str, typer.Option(help="Supported ingestion source")] = None,
):
    if active_ingestion:
        content = requests.get_active_ingestion_source()
        format_option.print(content=Ingestion(content), title=f"Active Ingestion Source: {content['source']}")

    if source:
        ingestion_config = Ingestion(requests.get_ingestion_source(source))
        format_option.print(content=ingestion_config, title=f"Ingestion Source : {source}")

    if not (source or active_ingestion):
        ingestion_sources = Ingestion(requests.get_ingestion_sources())
        format_option.print(content=ingestion_sources, title="Ingestion Sources")


@app.command()
def alerters(
    format_option: Annotated[FormatOptions, typer.Option("--format", "-f", help="specify display format")] = "table",
):
    """Display supported alerters."""
    pass
