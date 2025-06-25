"""
This command group provides visibility into BuffaLogs' available configurations,
such as supported alerters, ingestors and configuration schema.

Useful for inspecting system capabilities or integrating BuffaLogs with external tools.
"""

from typing import Annotated
from urllib.parse import urljoin

import requests
import typer
from buffacli import config
from buffacli.show.formatters import FormatOptions

app = typer.Typer(help="Show supported components and system metadata from BuffaLogs.")

root_url = config.get_buffalogs_url()

from rich.console import Console

console = Console()


@app.command()
def alert_types(
    format_option: Annotated[FormatOptions, typer.Option("--format", "-f", help="specify display format")] = "table",
    include_description: Annotated[bool, typer.Option(help="Include alert types description.")] = False,
):
    """Display supported alert types."""
    url = urljoin(root_url, "api/alert_types")
    alert_types = requests.get(url).json()
    if include_description:
        format_option.formatter(alert_types, title="Supported Alert Types", headers=["alert_type", "description"])
    else:
        format_option.formatter(alert_types, title="Supported Alert Types", headers=["alert_type"])


@app.command()
def alerters():
    """Display supported alerters."""
    pass


@app.command()
def ingestors():
    """Display supported ingestors."""
    pass
