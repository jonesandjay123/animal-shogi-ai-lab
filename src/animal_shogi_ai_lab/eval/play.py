from __future__ import annotations

from animal_shogi_ai_lab.engine import Action, GameState, MoveAction, Player
from animal_shogi_ai_lab.training import (
    decode_action,
    encode_observation,
    legal_action_mask,
)


def format_action_human(state: GameState, action: Action) -> str:
    """Formats an Action into a clean, human-readable string."""
    if isinstance(action, MoveAction):
        piece = state.board.get(action.from_square)
        piece_name = piece.kind.value if piece else "PIECE"
        target_piece = state.board.get(action.to_square)
        op = "captures" if target_piece else "moves to"
        from_str = f"({action.from_square.file},{action.from_square.rank})"
        to_str = f"({action.to_square.file},{action.to_square.rank})"
        return f"{piece_name} at {from_str} {op} {to_str}"
    else:
        to_str = f"({action.to_square.file},{action.to_square.rank})"
        return f"Drop {action.piece_kind.value} on {to_str}"


def play_vs_model(model_path: str, human_side: str = "BLACK") -> None:
    """Starts a terminal-based interactive game session against a trained model."""
    try:
        from sb3_contrib import MaskablePPO
    except ImportError:
        print("Error: stable-baselines3 and sb3-contrib are required to play against a model.")
        print("Please install the reinforcement learning dependencies by running:")
        print("  pip install -e \".[dev,ui,rl]\"")
        return

    print(f"Loading AI model from: {model_path}...")
    try:
        model = MaskablePPO.load(model_path)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    human_player = Player.BLACK if human_side.upper() == "BLACK" else Player.WHITE
    state = GameState.initial()

    print("\n" + "=" * 50)
    print(f"   Play vs AI Model (You: {human_player.value})")
    print("=" * 50 + "\n")

    while not state.is_terminal():
        print(state.render_ascii())
        print()
        active_player = state.side_to_move
        legal = state.legal_actions()
        if not legal:
            break

        if active_player is human_player:
            print("Your turn! Choose an action:")
            for idx, act in enumerate(legal):
                print(f"  [{idx + 1}] {format_action_human(state, act)}")

            while True:
                try:
                    choice = input(f"\nSelect action (1-{len(legal)}) or 'q' to quit: ").strip()
                    if choice.lower() == "q":
                        print("Quitting game...")
                        return
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(legal):
                        action = legal[choice_idx]
                        break
                    else:
                        print("Invalid index. Please select a valid option.")
                except ValueError:
                    print("Please enter a valid number or 'q'.")

            # Apply user action
            action_desc = format_action_human(state, action)
            state = state.apply_action(action)
            print(f"\nYou played: {action_desc}")
            print("-" * 50 + "\n")
        else:
            print("AI is thinking...")
            obs = encode_observation(state)
            mask = legal_action_mask(state)
            # Predict AI action
            action_idx, _ = model.predict(obs, action_masks=mask, deterministic=True)
            action = decode_action(int(action_idx))

            if action not in legal:
                print("AI attempted an illegal action! Declaring victory for Human.")
                break

            action_desc = format_action_human(state, action)
            state = state.apply_action(action)
            print(f"AI played: {action_desc}")
            print("-" * 50 + "\n")

    # Game finished
    print("=" * 50)
    print("   GAME OVER")
    print("=" * 50 + "\n")
    print(state.render_ascii())
    print()

    res = state.terminal_result()
    if res is not None:
        if res.winner is None:
            print("Result: Draw!")
        elif res.winner is human_player:
            print("Result: Congratulations! You won!")
        else:
            print("Result: AI won! Better luck next time.")
    else:
        print("Result: Game ended.")
    print("=" * 50)
