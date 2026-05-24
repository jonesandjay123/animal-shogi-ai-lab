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
    TerminalResult,
    render_ascii,
)


def state_with(
    board: dict[Square, Piece],
    *,
    side_to_move: Player = Player.BLACK,
    hands: dict[Player, dict[PieceKind, int]] | None = None,
    terminal_result: TerminalResult | None = None,
) -> GameState:
    return GameState.from_parts(
        board=board,
        side_to_move=side_to_move,
        hands=hands,
        terminal_result=terminal_result,
    )


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


def test_terminal_state_has_no_legal_actions_and_rejects_apply_action() -> None:
    state = state_with(
        {
            Square(1, 1): Piece(Player.BLACK, PieceKind.LION),
            Square(1, 2): Piece(Player.WHITE, PieceKind.LION),
        }
    ).apply_action(MoveAction(Square(1, 1), Square(1, 2)))

    assert state.legal_actions() == []
    with pytest.raises(ValueError):
        state.apply_action(MoveAction(Square(1, 2), Square(1, 3)))


def test_white_chick_promotes_when_moving_to_black_home_rank() -> None:
    state = state_with(
        {Square(1, 1): Piece(Player.WHITE, PieceKind.CHICK)},
        side_to_move=Player.WHITE,
    )

    next_state = state.apply_action(MoveAction(Square(1, 1), Square(1, 0)))

    assert next_state.board[Square(1, 0)] == Piece(Player.WHITE, PieceKind.HEN)


def test_white_chick_drop_on_black_home_rank_does_not_promote() -> None:
    state = state_with(
        {},
        side_to_move=Player.WHITE,
        hands={Player.WHITE: {PieceKind.CHICK: 1}},
    )

    next_state = state.apply_action(DropAction(PieceKind.CHICK, Square(1, 0)))

    assert next_state.board[Square(1, 0)] == Piece(Player.WHITE, PieceKind.CHICK)


@pytest.mark.parametrize("piece_kind", [PieceKind.LION, PieceKind.HEN])
def test_illegal_drop_piece_kind_is_rejected(piece_kind: PieceKind) -> None:
    state = state_with(
        {},
        hands={Player.BLACK: {PieceKind.CHICK: 1, PieceKind.GIRAFFE: 1, PieceKind.ELEPHANT: 1}},
    )

    assert DropAction(piece_kind, Square(0, 0)) not in state.legal_actions()
    with pytest.raises(ValueError):
        state.apply_action(DropAction(piece_kind, Square(0, 0)))


def test_cannot_drop_when_hand_count_is_zero() -> None:
    state = state_with({})

    assert DropAction(PieceKind.CHICK, Square(0, 0)) not in state.legal_actions()
    with pytest.raises(ValueError):
        state.apply_action(DropAction(PieceKind.CHICK, Square(0, 0)))


def test_move_from_empty_square_is_rejected() -> None:
    state = state_with({})

    with pytest.raises(ValueError):
        state.apply_action(MoveAction(Square(0, 0), Square(0, 1)))


def test_move_opponent_piece_is_rejected() -> None:
    state = state_with({Square(0, 0): Piece(Player.WHITE, PieceKind.LION)})

    with pytest.raises(ValueError):
        state.apply_action(MoveAction(Square(0, 0), Square(0, 1)))


def test_move_to_own_piece_square_is_rejected() -> None:
    state = state_with(
        {
            Square(1, 1): Piece(Player.BLACK, PieceKind.CHICK),
            Square(1, 2): Piece(Player.BLACK, PieceKind.GIRAFFE),
        }
    )

    with pytest.raises(ValueError):
        state.apply_action(MoveAction(Square(1, 1), Square(1, 2)))


def test_deserialized_repetition_history_can_still_trigger_draw() -> None:
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
    ]:
        state = state.apply_action(action)

    state = GameState.deserialize(json.loads(json.dumps(state.serialize())))

    for action in [
        MoveAction(Square(0, 0), Square(1, 0)),
        MoveAction(Square(2, 3), Square(1, 3)),
        MoveAction(Square(1, 0), Square(0, 0)),
        MoveAction(Square(1, 3), Square(2, 3)),
    ]:
        state = state.apply_action(action)

    assert state.terminal_result() == TerminalResult(TerminalReason.REPETITION_DRAW, None)


def test_repetition_key_includes_board_hands_and_side_to_move() -> None:
    base = state_with(
        {
            Square(0, 0): Piece(Player.BLACK, PieceKind.LION),
            Square(2, 3): Piece(Player.WHITE, PieceKind.LION),
        }
    )
    different_board = state_with(
        {
            Square(1, 0): Piece(Player.BLACK, PieceKind.LION),
            Square(2, 3): Piece(Player.WHITE, PieceKind.LION),
        }
    )
    different_hands = state_with(
        {
            Square(0, 0): Piece(Player.BLACK, PieceKind.LION),
            Square(2, 3): Piece(Player.WHITE, PieceKind.LION),
        },
        hands={Player.BLACK: {PieceKind.CHICK: 1}},
    )
    different_side = state_with(
        {
            Square(0, 0): Piece(Player.BLACK, PieceKind.LION),
            Square(2, 3): Piece(Player.WHITE, PieceKind.LION),
        },
        side_to_move=Player.WHITE,
    )

    assert base.state_key() != different_board.state_key()
    assert base.state_key() != different_hands.state_key()
    assert base.state_key() != different_side.state_key()


def test_render_ascii_initial_state_snapshot() -> None:
    assert render_ascii(GameState.initial()) == "\n".join(
        [
            "White hand: -",
            "r3 | g l e",
            "r2 | . c .",
            "r1 | . C .",
            "r0 | E L G",
            "     f0 f1 f2",
            "Black hand: -",
            "Turn: BLACK",
        ]
    )


def test_render_ascii_includes_hands_and_terminal_result() -> None:
    state = state_with(
        {
            Square(0, 0): Piece(Player.BLACK, PieceKind.LION),
            Square(1, 3): Piece(Player.WHITE, PieceKind.LION),
            Square(2, 2): Piece(Player.BLACK, PieceKind.HEN),
        },
        hands={
            Player.BLACK: {PieceKind.CHICK: 2, PieceKind.ELEPHANT: 1},
            Player.WHITE: {PieceKind.GIRAFFE: 1},
        },
        terminal_result=TerminalResult(TerminalReason.SAFE_TRY, Player.BLACK),
    )

    assert state.render_ascii() == "\n".join(
        [
            "White hand: G x1",
            "r3 | . l .",
            "r2 | . . H",
            "r1 | . . .",
            "r0 | L . .",
            "     f0 f1 f2",
            "Black hand: C x2, E x1",
            "Turn: BLACK",
            "Terminal: SAFE_TRY winner=BLACK",
        ]
    )
