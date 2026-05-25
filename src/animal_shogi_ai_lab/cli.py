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
def debug_board(
    model: str = typer.Option(None, help="Path to the trained PPO model zip file"),
    ai_side: str = typer.Option("WHITE", help="AI side: BLACK, WHITE, or BOTH"),
) -> None:
    """Launch the Pygame debug board (supports playing against a trained model)."""
    from animal_shogi_ai_lab.debug_ui.pygame_board import run_debug_board

    run_debug_board(model_path=model, ai_side=ai_side)


@app.command("self-play-random")
def self_play_random(games: int = typer.Option(100, help="Number of games to play")) -> None:
    """Run automated self-play using random agents."""
    from animal_shogi_ai_lab.agents import run_random_self_play

    typer.echo(f"Running {games} random self-play games...")
    stats = run_random_self_play(games)
    typer.echo("Results:")
    typer.echo(f"  Black wins: {stats['black_wins']}")
    typer.echo(f"  White wins: {stats['white_wins']}")
    typer.echo(f"  Draws: {stats['draws']}")
    typer.echo(f"  Average length: {stats['average_length']:.2f} plies")


@app.command("train-ppo")
def train_ppo_cmd(timesteps: int = typer.Option(1000, help="Number of training timesteps")) -> None:
    """Train a PPO model on the environment."""
    from animal_shogi_ai_lab.training import train_ppo

    train_ppo(timesteps)


@app.command("train-maskable-ppo")
def train_maskable_ppo_cmd(
    timesteps: int = typer.Option(100000, help="Number of training timesteps"),
    n_envs: int = typer.Option(8, help="Number of parallel environments"),
    seed: int = typer.Option(0, help="Random seed for environments and models"),
) -> None:
    """Train a MaskablePPO model with action masking on the environment."""
    from animal_shogi_ai_lab.training import train_maskable_ppo

    train_maskable_ppo(timesteps=timesteps, n_envs=n_envs, seed=seed)


@app.command("evaluate-random")
def evaluate_random_cmd(
    games: int = typer.Option(100, help="Number of games to evaluate")
) -> None:
    """Run a baseline evaluation of RandomAgent vs RandomAgent."""
    from animal_shogi_ai_lab.eval import evaluate_random

    evaluate_random(games)


@app.command("evaluate-model")
def evaluate_model_cmd(
    model: str = typer.Option(..., help="Path to the saved model zip file"),
    games: int = typer.Option(100, help="Number of games to evaluate"),
) -> None:
    """Evaluate a trained MaskablePPO model against RandomAgent."""
    from animal_shogi_ai_lab.eval import evaluate_model

    evaluate_model(model, games)


@app.command("play-vs-model")
def play_vs_model_cmd(
    model: str = typer.Option(..., help="Path to the trained PPO model zip file"),
    side: str = typer.Option("BLACK", help="Side you want to play: BLACK or WHITE"),
) -> None:
    """Start an interactive terminal-based game against a trained PPO model."""
    from animal_shogi_ai_lab.eval import play_vs_model

    play_vs_model(model_path=model, human_side=side)



