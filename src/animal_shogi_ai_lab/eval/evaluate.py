from __future__ import annotations

from typing import Any

from animal_shogi_ai_lab.agents import HeuristicAgent, RandomAgent, run_random_self_play
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


def evaluate_model(
    model_path: str,
    games: int = 100,
    side: str = "BOTH",
    opponent_type: str = "random",
    opponent_model_path: str | None = None,
) -> dict[str, Any] | None:
    """Evaluates a trained MaskablePPO model against a fixed opponent.

    Supports ``opponent_type`` "random", "heuristic", or "model" (a frozen
    MaskablePPO loaded from ``opponent_model_path``), and evaluating strictly
    as BLACK, WHITE, or alternating BOTH sides.
    """
    try:
        from sb3_contrib import MaskablePPO
    except ImportError:
        print("Error: stable-baselines3 and sb3-contrib are required to evaluate a model.")
        print("Please install the reinforcement learning dependencies by running:")
        print("  pip install -e \".[dev,ui,rl]\"")
        return None

    opponent_name = opponent_type.lower()
    if opponent_name == "random":
        opponent = RandomAgent()
    elif opponent_name == "heuristic":
        opponent = HeuristicAgent()
    elif opponent_name == "model":
        if opponent_model_path is None:
            print("opponent=model requires --opponent-model <path to model zip>.")
            return None
        from animal_shogi_ai_lab.agents.model_agent import ModelOpponentAgent

        print(f"Loading opponent model from: {opponent_model_path}")
        # Stochastic opponent, otherwise every deterministic-vs-deterministic
        # game is identical and the win rate is meaningless.
        opponent = ModelOpponentAgent(model_path=opponent_model_path, deterministic=False)
        opponent_name = "model"
    else:
        print(f"Unknown opponent type: {opponent_type}. Use 'random', 'heuristic', or 'model'.")
        return None

    print(f"Loading model from: {model_path}")
    try:
        model = MaskablePPO.load(model_path)
    except Exception as e:
        print(f"Failed to load model from {model_path}: {e}")
        return None

    model_wins = 0
    opponent_wins = 0
    draws = 0
    invalid_actions = 0
    total_ply = 0

    eval_side = side.upper()
    print(
        f"Starting evaluation of {games} games against {opponent_name} opponent "
        f"(Model Side: {eval_side})..."
    )

    for i in range(games):
        # Choose side
        if eval_side == "BLACK":
            model_player = Player.BLACK
        elif eval_side == "WHITE":
            model_player = Player.WHITE
        else:
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
                # Opponent's turn
                action = opponent.select_action(state, legal)
                state = state.apply_action(action)

        total_ply += state.ply
        res = state.terminal_result()

        if res is not None:
            if res.winner is None:
                draws += 1
            elif res.winner is model_player:
                model_wins += 1
            else:
                opponent_wins += 1
        else:
            # Model made an invalid action or terminated without result
            opponent_wins += 1

    win_rate = model_wins / games if games > 0 else 0.0
    avg_length = total_ply / games if games > 0 else 0.0

    print("\nResults:")
    print(f"  Total Games: {games}")
    print(f"  Opponent: {opponent_name}")
    print(f"  Model Wins: {model_wins}")
    print(f"  Opponent Wins: {opponent_wins}")
    print(f"  Draws: {draws}")
    print(f"  Model Win Rate: {win_rate * 100:.2f}%")
    print(f"  Invalid Actions by Model: {invalid_actions}")
    print(f"  Average Game Length: {avg_length:.2f} plies")

    return {
        "games": games,
        "opponent": opponent_name,
        "side": eval_side,
        "model_wins": model_wins,
        "opponent_wins": opponent_wins,
        "draws": draws,
        "win_rate": win_rate,
        "invalid_actions": invalid_actions,
        "average_length": avg_length,
    }
