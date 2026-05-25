from __future__ import annotations

import random
from collections.abc import Sequence
from typing import Any

from animal_shogi_ai_lab.engine import Action, GameState, Player


class RandomAgent:
    """An agent that chooses randomly among all legal actions."""

    def select_action(self, state: GameState, legal_actions: Sequence[Action]) -> Action:
        if not legal_actions:
            raise ValueError("No legal actions available.")
        return random.choice(legal_actions)


def run_random_self_play(num_games: int = 100) -> dict[str, Any]:
    """Runs a series of automated self-play games using RandomAgent."""
    black_wins = 0
    white_wins = 0
    draws = 0
    total_ply = 0
    agent = RandomAgent()

    for _ in range(num_games):
        state = GameState.initial()
        while not state.is_terminal():
            legal = state.legal_actions()
            if not legal:
                break
            action = agent.select_action(state, legal)
            state = state.apply_action(action)

        total_ply += state.ply
        res = state.terminal_result()
        if res is not None:
            if res.winner is None:
                draws += 1
            elif res.winner is Player.BLACK:
                black_wins += 1
            elif res.winner is Player.WHITE:
                white_wins += 1
        else:
            # Fallback if no terminal result is set
            draws += 1

    avg_length = total_ply / num_games if num_games > 0 else 0.0

    return {
        "games": num_games,
        "black_wins": black_wins,
        "white_wins": white_wins,
        "draws": draws,
        "average_length": avg_length,
    }
