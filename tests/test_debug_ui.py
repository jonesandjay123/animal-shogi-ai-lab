from animal_shogi_ai_lab.debug_ui.pygame_board import (
    DebugBoardSession,
    build_legal_action_maps,
)
from animal_shogi_ai_lab.engine import DropAction, GameState, MoveAction, PieceKind, Square


def test_build_legal_action_maps_groups_moves_and_drops() -> None:
    move = MoveAction(Square(1, 1), Square(1, 2))
    drop = DropAction(PieceKind.CHICK, Square(0, 0))

    maps = build_legal_action_maps([move, drop])

    assert maps.moves_by_from == {Square(1, 1): {Square(1, 2): move}}
    assert maps.drops_by_kind == {PieceKind.CHICK: {Square(0, 0): drop}}


def test_debug_board_session_apply_and_undo() -> None:
    session = DebugBoardSession.initial()
    initial_state = session.state
    action = MoveAction(Square(1, 1), Square(1, 2))

    session.apply_action(action)

    assert session.state != initial_state
    assert session.history == [initial_state]
    assert session.move_log == ["move 1,1 -> 1,2"]

    assert session.undo()
    assert session.state == initial_state
    assert session.history == []
    assert session.move_log == []


def test_debug_board_session_save_and_load(tmp_path) -> None:
    path = tmp_path / "state.json"
    session = DebugBoardSession.initial()
    action = MoveAction(Square(1, 1), Square(1, 2))
    session.apply_action(action)
    saved_state = session.state

    session.save(path)
    session.reset()
    assert session.state == GameState.initial()

    assert session.load(path)
    assert session.state == saved_state
    assert session.history == []
    assert session.move_log == []


def test_debug_board_session_load_missing_file(tmp_path) -> None:
    session = DebugBoardSession.initial()

    assert not session.load(tmp_path / "missing.json")
    assert session.state == GameState.initial()
    assert "No save file" in session.status_message
