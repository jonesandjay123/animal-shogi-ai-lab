from __future__ import annotations

import random
from typing import Any

from animal_shogi_ai_lab.agents import run_random_self_play
from animal_shogi_ai_lab.engine import GameState, Player
from animal_shogi_ai_lab.training import (
    decode_action,
    encode_observation,
    legal_action_mask,
)


def evaluate_random(games: int = 100) -> None:
    """Runs a baseline evaluation of RandomAgent vs RandomAgent."""
    print(f"Running {games} games of Random Agent vs Random Agent...")
    stats = run_random_self_play(games)
    print("\nResults:")
    print(f"  Total Games: {stats['games']}")
    print(f"  Black (Random) Wins: {stats['black_wins']}")
    print(f"  White (Random) Wins: {stats['white_wins']}")
    print(f"  Draws: {stats['draws']}")
    print(f"  Average Game Length: {stats['average_length']:.2f} plies")


def evaluate_model(model_path: str, games: int = 100) -> dict[str, Any] | None:
    """Evaluates a trained MaskablePPO model against a RandomAgent.

    Alternates player roles (Model as Black, then Model as White) for fair evaluation.
    """
    try:
        from sb3_contrib import MaskablePPO
    except ImportError:
        print("Error: stable-baselines3 and sb3-contrib are required to evaluate a model.")
        print("Please install the reinforcement learning dependencies by running:")
        print("  pip install -e \".[dev,ui,rl]\"")
        return None

    print(f"Loading model from: {model_path}")
    try:
        model = MaskablePPO.load(model_path)
    except Exception as e:
        print(f"Failed to load model from {model_path}: {e}")
        return None

    model_wins = 0
    random_wins = 0
    draws = 0
    invalid_actions = 0
    total_ply = 0

    print(f"Starting evaluation of {games} games against RandomAgent...")

    for i in range(games):
        # Alternate roles: Model is BLACK on even games, WHITE on odd games.
        model_player = Player.BLACK if i % 2 == 0 else Player.WHITE

        state = GameState.initial()
        while not state.is_terminal():
            active_player = state.side_to_move
            legal = state.legal_actions()
            if not legal:
                break

            if active_player is model_player:
                # Model's turn
                obs = encode_observation(state)
                mask = legal_action_mask(state)
                # Predict action index using the legal action mask
                action_idx, _ = model.predict(obs, action_masks=mask, deterministic=True)
                action = decode_action(int(action_idx))

                # Safeguard against predicting illegal action
                if action not in legal:
                    invalid_actions += 1
                    # Declare model loss on illegal move
                    state = GameState.from_parts(
                        board=state.board,
                        side_to_move=state.side_to_move,
                        hands=state.hands,
                        ply=state.ply,
                        terminal_result=None,  # Handled as loss below
                    )
                    break

                state = state.apply_action(action)
            else:
                # Random agent's turn
                action = random.choice(legal)
                state = state.apply_action(action)

        total_ply += state.ply
        res = state.terminal_result()

        if res is not None:
            if res.winner is None:
                draws += 1
            elif res.winner is model_player:
                model_wins += 1
            else:
                random_wins += 1
        else:
            # Model made an invalid action or terminated without result
            random_wins += 1

    win_rate = model_wins / games if games > 0 else 0.0
    avg_length = total_ply / games if games > 0 else 0.0

    print("\nResults:")
    print(f"  Total Games: {games}")
    print(f"  Model Wins: {model_wins} (as Black: {model_wins if games % 2 == 0 else 'N/A'})")
    print(f"  Random Agent Wins: {random_wins}")
    print(f"  Draws: {draws}")
    print(f"  Model Win Rate: {win_rate * 100:.2f}%")
    print(f"  Invalid Actions by Model: {invalid_actions}")
    print(f"  Average Game Length: {avg_length:.2f} plies")

    return {
        "games": games,
        "model_wins": model_wins,
        "random_wins": random_wins,
        "draws": draws,
        "win_rate": win_rate,
        "invalid_actions": invalid_actions,
        "average_length": avg_length,
    }
