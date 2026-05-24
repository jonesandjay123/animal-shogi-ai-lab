from animal_shogi_ai_lab.debug_ui.pygame_board import build_legal_action_maps
from animal_shogi_ai_lab.engine import DropAction, MoveAction, PieceKind, Square


def test_build_legal_action_maps_groups_moves_and_drops() -> None:
    move = MoveAction(Square(1, 1), Square(1, 2))
    drop = DropAction(PieceKind.CHICK, Square(0, 0))

    maps = build_legal_action_maps([move, drop])

    assert maps.moves_by_from == {Square(1, 1): {Square(1, 2): move}}
    assert maps.drops_by_kind == {PieceKind.CHICK: {Square(0, 0): drop}}
