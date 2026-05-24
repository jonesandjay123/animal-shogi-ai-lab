from __future__ import annotations

import typer

from animal_shogi_ai_lab import __version__

app = typer.Typer(help="Animal Shogi AI Lab command line tools.")


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)


@app.command()
def status() -> None:
    """Print the current scaffold status."""
    typer.echo("Scaffold ready. Core game logic is not implemented yet.")
