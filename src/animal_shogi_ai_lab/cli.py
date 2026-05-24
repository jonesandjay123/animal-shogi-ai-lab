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
    typer.echo("Clean engine ready. Debug UI available with the ui extra.")


@app.command("debug-board")
def debug_board() -> None:
    """Launch the Pygame human self-play debug board."""
    from animal_shogi_ai_lab.debug_ui.pygame_board import run_debug_board

    run_debug_board()
