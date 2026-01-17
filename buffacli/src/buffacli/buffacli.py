from pathlib import Path
from typing import Annotated

import typer

from buffacli import config
from buffacli.commands import query, show
from buffacli.globals import VLevel, set_verbose_level

app = typer.Typer()

app.add_typer(show.app, name="show")
app.add_typer(query.app, name="query")


@app.callback()
def callback(
    verbose_level: Annotated[
        VLevel, typer.Option("-v", "--verbose", help="Verbose level")
    ] = None
):
    verbose_level = (
        verbose_level.value
        if verbose_level
        else config.read_from_config("verbose_level")
    )
    set_verbose_level(verbose_level)


@app.command()
def setup(
    buffalogs_url: Annotated[str, typer.Option(help="Base URL for buffalogs.")] = None,
    config_path: Annotated[
        Path,
        typer.Option(
            exists=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help="ini config file path",
        ),
    ] = None,
    verbose_level: Annotated[
        int, typer.Option("-v", "--verbose", help="Verbose level")
    ] = None,
):
    """Configure BuffaCLI-specific setups."""
    if buffalogs_url:
        config.write_to_config("buffalogs_url", buffalogs_url)
    if verbose_level:
        config.write_to_config("verbose_level", verbose_level)
    if config_path:
        config.write_to_config("custom_config_path", str(config_path.resolve()))


if __name__ == "__main__":
    app()
