from pathlib import Path
from typing import Annotated

import typer
from buffacli import config, show

app = typer.Typer()

app.add_typer(show.app, name="show")


@app.command()
def setup(
    buffalogs_url: Annotated[str, typer.Option(help="Base URL for buffalogs.")] = None,
    config_path: Annotated[Path, typer.Option(exists=True, dir_okay=False, readable=True, resolve_path=True, help="ini config file path")] = None,
):
    """Configure BuffaCLI-specific setups."""
    if buffalogs_url:
        config.write_to_config("buffalogs_url", buffalogs_url)
    if config_path:
        config.write_to_config("custom_config_path", str(config_path.resolve()))


if __name__ == "__main__":
    app()
