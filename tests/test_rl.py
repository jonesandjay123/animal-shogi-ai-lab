from __future__ import annotations

import numpy as np

from animal_shogi_ai_lab.agents import RandomAgent, run_random_self_play
from animal_shogi_ai_lab.engine import (
    DropAction,
    GameState,
    MoveAction,
    Piece,
    PieceKind,
    Player,
    Square,
)
from animal_shogi_ai_lab.training import (
    AnimalShogiEnv,
    decode_action,
    encode_action,
    encode_observation,
    legal_action_mask,
)


def test_random_agent_selects_legal_actions() -> None:
    agent = RandomAgent()
    state = GameState.initial()
    legal = state.legal_actions()
    action = agent.select_action(state, legal)
    assert action in legal


def test_self_play_runs_successfully() -> None:
    stats = run_random_self_play(num_games=5)
    assert stats["games"] == 5
    assert stats["black_wins"] + stats["white_wins"] + stats["draws"] == 5
    assert stats["average_length"] >= 0.0


def test_action_encoding_round_trip() -> None:
    state = GameState.initial()
    for action in state.legal_actions():
        encoded = encode_action(action)
        assert 0 <= encoded < 132
        decoded = decode_action(encoded)
        assert decoded == action


def test_all_possible_decodings_and_encodings() -> None:
    # Test all 132 slots are decodable and can be encoded back
    # if they are syntactically valid moves/drops
    for i in range(132):
        action = decode_action(i)
        if isinstance(action, MoveAction):
            assert 0 <= action.from_square.file < 3
            assert 0 <= action.from_square.rank < 4
            assert encode_action(action) == i
        elif isinstance(action, DropAction):
            assert 0 <= action.to_square.file < 3
            assert 0 <= action.to_square.rank < 4
            assert action.piece_kind in [PieceKind.CHICK, PieceKind.GIRAFFE, PieceKind.ELEPHANT]
            assert encode_action(action) == i


def test_legal_action_mask() -> None:
    state = GameState.initial()
    mask = legal_action_mask(state)
    assert mask.shape == (132,)
    assert mask.dtype == np.bool_

    legal_indices = [encode_action(act) for act in state.legal_actions()]
    for i in range(132):
        if i in legal_indices:
            assert mask[i]
        else:
            assert not mask[i]


def test_legal_action_mask_terminal() -> None:
    # Create a simple terminal state by capturing the opponent Lion
    board = {
        Square(1, 1): Piece(Player.BLACK, PieceKind.LION),
        Square(1, 2): Piece(Player.WHITE, PieceKind.LION),
    }
    state = GameState.from_parts(board=board, side_to_move=Player.BLACK)
    terminal_state = state.apply_action(MoveAction(Square(1, 1), Square(1, 2)))
    assert terminal_state.is_terminal()

    mask = legal_action_mask(terminal_state)
    assert not np.any(mask)  # All False


def test_observation_encoding() -> None:
    state = GameState.initial()
    obs = encode_observation(state)
    assert obs.shape == (126,)
    assert obs.dtype == np.float32

    # Reconstruction check
    planes = obs[:120].reshape((10, 4, 3))
    assert planes[0, 0, 1] == 1.0  # own Lion at (1, 0)
    assert planes[1, 0, 2] == 1.0  # own Giraffe at (2, 0)
    assert planes[2, 0, 0] == 1.0  # own Elephant at (0, 0)
    assert planes[3, 1, 1] == 1.0  # own Chick at (1, 1)

    assert planes[5, 3, 1] == 1.0  # opponent Lion at (1, 3)
    assert planes[6, 3, 0] == 1.0  # opponent Giraffe at (0, 3)
    assert planes[7, 3, 2] == 1.0  # opponent Elephant at (2, 3)
    assert planes[8, 2, 1] == 1.0  # opponent Chick at (1, 2)

    assert np.all(obs[120:] == 0.0)  # no hand counts initially


def test_observation_perspective_normalization() -> None:
    board = {Square(0, 0): Piece(Player.BLACK, PieceKind.LION)}

    state_black = GameState.from_parts(board=board, side_to_move=Player.BLACK)
    obs_black = encode_observation(state_black)[:120].reshape((10, 4, 3))
    assert obs_black[0, 0, 0] == 1.0  # own Lion at (0, 0)

    state_white = GameState.from_parts(board=board, side_to_move=Player.WHITE)
    obs_white = encode_observation(state_white)[:120].reshape((10, 4, 3))
    assert obs_white[5, 3, 2] == 1.0  # opponent Lion at (2, 3) (flipped)


def test_gym_env_flow() -> None:
    env = AnimalShogiEnv()
    obs, info = env.reset()
    assert obs.shape == (126,)
    assert "action_mask" in info
    assert info["action_mask"].shape == (132,)

    legal_indices = np.where(info["action_mask"])[0]
    assert len(legal_indices) > 0
    action_idx = legal_indices[0]

    next_obs, reward, terminated, truncated, next_info = env.step(action_idx)
    assert next_obs.shape == (126,)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert "action_mask" in next_info


def test_gym_env_invalid_action() -> None:
    env = AnimalShogiEnv()
    obs, info = env.reset()

    invalid_indices = np.where(~info["action_mask"])[0]
    assert len(invalid_indices) > 0
    action_idx = invalid_indices[0]

    next_obs, reward, terminated, truncated, next_info = env.step(action_idx)
    assert reward == -10.0
    assert terminated is True
    assert next_info["error"] == "illegal_action"


def test_env_action_masks() -> None:
    env = AnimalShogiEnv()
    env.reset()
    mask = env.action_masks()
    assert mask.shape == (132,)
    assert mask.dtype == np.bool_
    assert np.array_equal(mask, legal_action_mask(env.state))


def test_train_maskable_ppo_missing_dependency(capsys) -> None:
    import sys
    from unittest import mock

    from animal_shogi_ai_lab.training import train_maskable_ppo

    with mock.patch.dict(sys.modules, {"sb3_contrib": None}):
        train_maskable_ppo(timesteps=10)
        captured = capsys.readouterr()
        assert "stable-baselines3 and sb3-contrib are required" in captured.out


def test_evaluate_model_missing_dependency(capsys) -> None:
    import sys
    from unittest import mock

    from animal_shogi_ai_lab.eval import evaluate_model

    with mock.patch.dict(sys.modules, {"sb3_contrib": None}):
        res = evaluate_model("dummy_path", games=10)
        captured = capsys.readouterr()
        assert res is None
        assert "stable-baselines3 and sb3-contrib are required" in captured.out


def test_evaluate_random_smoke() -> None:
    from animal_shogi_ai_lab.eval import evaluate_random
    # Just run a quick evaluation to ensure it doesn't crash
    evaluate_random(games=2)


def test_play_vs_model_missing_dependency(capsys) -> None:
    import sys
    from unittest import mock

    from animal_shogi_ai_lab.eval import play_vs_model

    with mock.patch.dict(sys.modules, {"sb3_contrib": None}):
        play_vs_model("dummy_path", human_side="BLACK")
        captured = capsys.readouterr()
        assert "stable-baselines3 and sb3-contrib are required" in captured.out


def test_vs_opponent_env_reset() -> None:
    from animal_shogi_ai_lab.training.env_vs_opponent import AnimalShogiVsOpponentEnv
    # BLACK reset: starts immediately on BLACK's turn
    env_black = AnimalShogiVsOpponentEnv(learning_player=Player.BLACK)
    obs, info = env_black.reset()
    assert env_black.state.side_to_move == Player.BLACK
    assert env_black.state.ply == 0

    # WHITE reset: opponent plays BLACK's move automatically, transitioning to WHITE's turn
    env_white = AnimalShogiVsOpponentEnv(learning_player=Player.WHITE)
    obs, info = env_white.reset()
    assert env_white.state.side_to_move == Player.WHITE
    assert env_white.state.ply == 1


def test_vs_opponent_env_step_advances_two_plies() -> None:
    from animal_shogi_ai_lab.training.env_vs_opponent import AnimalShogiVsOpponentEnv
    env = AnimalShogiVsOpponentEnv(learning_player=Player.BLACK)
    obs, info = env.reset()
    assert env.state.side_to_move == Player.BLACK

    # Execute a move
    legal_indices = np.where(info["action_mask"])[0]
    action_idx = legal_indices[0]

    obs_next, reward, terminated, truncated, info_next = env.step(action_idx)

    # Game should either be terminal or back to BLACK's turn (since White opponent responded)
    if not terminated:
        assert env.state.side_to_move == Player.BLACK
        assert env.state.ply == 2
        assert reward == -0.001
    else:
        assert reward in [1.0, -1.0, 0.0]


def test_train_maskable_ppo_vs_random_missing_dependency(capsys) -> None:
    import sys
    from unittest import mock

    from animal_shogi_ai_lab.training.train_maskable_ppo_vs_random import (
        train_maskable_ppo_vs_random,
    )

    with mock.patch.dict(sys.modules, {"sb3_contrib": None}):
        train_maskable_ppo_vs_random(side="BLACK", timesteps=10)
        captured = capsys.readouterr()
        assert "stable-baselines3 and sb3-contrib are required" in captured.out



