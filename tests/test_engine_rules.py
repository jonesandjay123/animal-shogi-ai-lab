import json

import pytest

from animal_shogi_ai_lab.engine import (
    DropAction,
    GameState,
    MoveAction,
    Piece,
    PieceKind,
    Player,
    Square,
    TerminalReason,
)


def state_with(
    board: dict[Square, Piece],
    *,
    side_to_move: Player = Player.BLACK,
    hands: dict[Player, dict[PieceKind, int]] | None = None,
) -> GameState:
    return GameState.from_parts(board=board, side_to_move=side_to_move, hands=hands)


def destinations(state: GameState, origin: Square) -> set[Square]:
    return {
        action.to_square
        for action in state.legal_actions()
        if isinstance(action, MoveAction) and action.from_square == origin
    }


def test_initial_board_matches_rules_spec() -> None:
    state = GameState.initial()

    assert state.side_to_move == Player.BLACK
    assert state.hands == {
        Player.BLACK: {PieceKind.CHICK: 0, PieceKind.GIRAFFE: 0, PieceKind.ELEPHANT: 0},
        Player.WHITE: {PieceKind.CHICK: 0, PieceKind.GIRAFFE: 0, PieceKind.ELEPHANT: 0},
    }
    assert state.board == {
        Square(0, 0): Piece(Player.BLACK, PieceKind.ELEPHANT),
        Square(1, 0): Piece(Player.BLACK, PieceKind.LION),
        Square(2, 0): Piece(Player.BLACK, PieceKind.GIRAFFE),
        Square(1, 1): Piece(Player.BLACK, PieceKind.CHICK),
        Square(1, 2): Piece(Player.WHITE, PieceKind.CHICK),
        Square(0, 3): Piece(Player.WHITE, PieceKind.GIRAFFE),
        Square(1, 3): Piece(Player.WHITE, PieceKind.LION),
        Square(2, 3): Piece(Player.WHITE, PieceKind.ELEPHANT),
    }


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        (
            PieceKind.LION,
            {
                Square(0, 0),
                Square(1, 0),
                Square(2, 0),
                Square(0, 1),
                Square(2, 1),
                Square(0, 2),
                Square(1, 2),
                Square(2, 2),
            },
        ),
        (
            PieceKind.GIRAFFE,
            {Square(1, 0), Square(0, 1), Square(2, 1), Square(1, 2)},
        ),
        (PieceKind.ELEPHANT, {Square(0, 0), Square(2, 0), Square(0, 2), Square(2, 2)}),
        (PieceKind.CHICK, {Square(1, 2)}),
        (
            PieceKind.HEN,
            {Square(0, 1), Square(2, 1), Square(0, 2), Square(1, 2), Square(2, 2), Square(1, 0)},
        ),
    ],
)
def test_black_piece_basic_moves(kind: PieceKind, expected: set[Square]) -> None:
    origin = Square(1, 1)
    state = state_with({origin: Piece(Player.BLACK, kind)})

    assert destinations(state, origin) == expected


def test_white_chick_moves_in_opposite_direction() -> None:
    origin = Square(1, 2)
    state = state_with({origin: Piece(Player.WHITE, PieceKind.CHICK)}, side_to_move=Player.WHITE)

    assert destinations(state, origin) == {Square(1, 1)}


def test_moves_do_not_leave_board() -> None:
    origin = Square(0, 0)
    state = state_with({origin: Piece(Player.BLACK, PieceKind.LION)})

    assert destinations(state, origin) == {Square(0, 1), Square(1, 0), Square(1, 1)}


def test_cannot_capture_own_piece() -> None:
    origin = Square(1, 1)
    occupied = Square(1, 2)
    state = state_with(
        {
            origin: Piece(Player.BLACK, PieceKind.CHICK),
            occupied: Piece(Player.BLACK, PieceKind.GIRAFFE),
        }
    )

    assert occupied not in destinations(state, origin)


def test_capture_adds_piece_to_hand() -> None:
    state = state_with(
        {
            Square(1, 1): Piece(Player.BLACK, PieceKind.CHICK),
            Square(1, 2): Piece(Player.WHITE, PieceKind.GIRAFFE),
        }
    )

    next_state = state.apply_action(MoveAction(Square(1, 1), Square(1, 2)))

    assert next_state.board[Square(1, 2)] == Piece(Player.BLACK, PieceKind.CHICK)
    assert next_state.hands[Player.BLACK][PieceKind.GIRAFFE] == 1


def test_captured_hen_demotes_to_chick_in_hand() -> None:
    state = state_with(
        {
            Square(1, 1): Piece(Player.BLACK, PieceKind.CHICK),
            Square(1, 2): Piece(Player.WHITE, PieceKind.HEN),
        }
    )

    next_state = state.apply_action(MoveAction(Square(1, 1), Square(1, 2)))

    assert next_state.hands[Player.BLACK][PieceKind.CHICK] == 1
    assert PieceKind.HEN not in next_state.hands[Player.BLACK]


def test_drop_places_hand_piece_on_empty_square() -> None:
    state = state_with(
        {},
        hands={Player.BLACK: {PieceKind.GIRAFFE: 1}, Player.WHITE: {}},
    )

    next_state = state.apply_action(DropAction(PieceKind.GIRAFFE, Square(0, 0)))

    assert next_state.board[Square(0, 0)] == Piece(Player.BLACK, PieceKind.GIRAFFE)
    assert next_state.hands[Player.BLACK][PieceKind.GIRAFFE] == 0


def test_cannot_drop_on_occupied_square() -> None:
    state = state_with(
        {Square(0, 0): Piece(Player.BLACK, PieceKind.LION)},
        hands={Player.BLACK: {PieceKind.CHICK: 1}, Player.WHITE: {}},
    )

    assert DropAction(PieceKind.CHICK, Square(0, 0)) not in state.legal_actions()
    with pytest.raises(ValueError):
        state.apply_action(DropAction(PieceKind.CHICK, Square(0, 0)))


def test_chick_promotes_when_moving_to_enemy_home_rank() -> None:
    state = state_with({Square(1, 2): Piece(Player.BLACK, PieceKind.CHICK)})

    next_state = state.apply_action(MoveAction(Square(1, 2), Square(1, 3)))

    assert next_state.board[Square(1, 3)] == Piece(Player.BLACK, PieceKind.HEN)


def test_chick_drop_on_enemy_home_rank_does_not_promote() -> None:
    state = state_with(
        {},
        hands={Player.BLACK: {PieceKind.CHICK: 1}, Player.WHITE: {}},
    )

    next_state = state.apply_action(DropAction(PieceKind.CHICK, Square(1, 3)))

    assert next_state.board[Square(1, 3)] == Piece(Player.BLACK, PieceKind.CHICK)


def test_capture_lion_immediately_wins() -> None:
    state = state_with(
        {
            Square(1, 1): Piece(Player.BLACK, PieceKind.LION),
            Square(1, 2): Piece(Player.WHITE, PieceKind.LION),
        }
    )

    next_state = state.apply_action(MoveAction(Square(1, 1), Square(1, 2)))

    assert next_state.is_terminal()
    assert next_state.terminal_result() is not None
    assert next_state.terminal_result().reason == TerminalReason.LION_CAPTURE
    assert next_state.terminal_result().winner == Player.BLACK
    assert PieceKind.LION not in next_state.hands[Player.BLACK]


def test_safe_try_wins() -> None:
    state = state_with(
        {
            Square(1, 2): Piece(Player.BLACK, PieceKind.LION),
            Square(2, 1): Piece(Player.WHITE, PieceKind.LION),
        }
    )

    next_state = state.apply_action(MoveAction(Square(1, 2), Square(1, 3)))

    assert next_state.is_terminal()
    assert next_state.terminal_result() is not None
    assert next_state.terminal_result().reason == TerminalReason.SAFE_TRY
    assert next_state.terminal_result().winner == Player.BLACK


def test_unsafe_try_does_not_immediately_win() -> None:
    state = state_with(
        {
            Square(0, 2): Piece(Player.BLACK, PieceKind.LION),
            Square(1, 3): Piece(Player.WHITE, PieceKind.GIRAFFE),
            Square(2, 1): Piece(Player.WHITE, PieceKind.LION),
        }
    )

    next_state = state.apply_action(MoveAction(Square(0, 2), Square(0, 3)))

    assert not next_state.is_terminal()
    assert next_state.side_to_move == Player.WHITE


def test_third_full_position_occurrence_is_draw() -> None:
    state = state_with(
        {
            Square(0, 0): Piece(Player.BLACK, PieceKind.LION),
            Square(2, 3): Piece(Player.WHITE, PieceKind.LION),
        }
    )

    for action in [
        MoveAction(Square(0, 0), Square(1, 0)),
        MoveAction(Square(2, 3), Square(1, 3)),
        MoveAction(Square(1, 0), Square(0, 0)),
        MoveAction(Square(1, 3), Square(2, 3)),
        MoveAction(Square(0, 0), Square(1, 0)),
        MoveAction(Square(2, 3), Square(1, 3)),
        MoveAction(Square(1, 0), Square(0, 0)),
        MoveAction(Square(1, 3), Square(2, 3)),
    ]:
        state = state.apply_action(action)

    assert state.is_terminal()
    assert state.terminal_result() is not None
    assert state.terminal_result().reason == TerminalReason.REPETITION_DRAW
    assert state.terminal_result().winner is None


def test_serialize_deserialize_round_trip() -> None:
    state = state_with(
        {
            Square(0, 0): Piece(Player.BLACK, PieceKind.LION),
            Square(1, 3): Piece(Player.WHITE, PieceKind.HEN),
        },
        side_to_move=Player.WHITE,
        hands={
            Player.BLACK: {PieceKind.CHICK: 1, PieceKind.ELEPHANT: 1},
            Player.WHITE: {PieceKind.GIRAFFE: 1},
        },
    )

    payload = json.loads(json.dumps(state.serialize()))
    restored = GameState.deserialize(payload)

    assert restored == state
