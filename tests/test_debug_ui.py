from pathlib import Path

from animal_shogi_ai_lab.debug_ui.assets import (
    PIECE_SPRITE_INDEX,
    SPRITE_SHEET_RELATIVE_PATH,
    default_sprite_sheet_path,
    load_piece_sprites,
)
from animal_shogi_ai_lab.debug_ui.pygame_board import (
    DebugBoardSession,
    _draw_piece,
    build_legal_action_maps,
)
from animal_shogi_ai_lab.engine import (
    DropAction,
    GameState,
    MoveAction,
    Piece,
    PieceKind,
    Player,
    Square,
)


def test_build_legal_action_maps_groups_moves_and_drops() -> None:
    move = MoveAction(Square(1, 1), Square(1, 2))
    drop = DropAction(PieceKind.CHICK, Square(0, 0))

    maps = build_legal_action_maps([move, drop])

    assert maps.moves_by_from == {Square(1, 1): {Square(1, 2): move}}
    assert maps.drops_by_kind == {PieceKind.CHICK: {Square(0, 0): drop}}


def test_piece_kind_to_sprite_index_mapping() -> None:
    assert PIECE_SPRITE_INDEX == {
        PieceKind.CHICK: 0,
        PieceKind.HEN: 1,
        PieceKind.LION: 2,
        PieceKind.GIRAFFE: 3,
        PieceKind.ELEPHANT: 4,
    }


def test_default_sprite_sheet_path_resolution() -> None:
    assert default_sprite_sheet_path().is_absolute()
    assert default_sprite_sheet_path().as_posix().endswith(SPRITE_SHEET_RELATIVE_PATH.as_posix())
    assert default_sprite_sheet_path().exists()


def test_missing_sprite_sheet_returns_empty_sprite_map(tmp_path) -> None:
    assert load_piece_sprites(object(), tmp_path / "missing.png") == {}


def test_sprite_sheet_loader_slices_horizontal_sheet(tmp_path) -> None:
    class FakeSurface:
        def __init__(self, name="sheet"):
            self.name = name

        def convert_alpha(self):
            return self

        def get_size(self):
            return (500, 100)

        def subsurface(self, rect):
            return FakeSubsurface(rect)

    class FakeSubsurface:
        def __init__(self, rect):
            self.rect = rect

        def copy(self):
            return self

    class FakeImage:
        @staticmethod
        def load(path):
            assert Path(path).name == "sheet.png"
            return FakeSurface()

    class FakePygame:
        image = FakeImage()

        @staticmethod
        def Rect(x, y, width, height):
            return (x, y, width, height)

    path = tmp_path / "sheet.png"
    path.write_bytes(b"fake")

    sprites = load_piece_sprites(FakePygame(), path)

    assert sprites[PieceKind.CHICK].rect == (0, 0, 100, 100)
    assert sprites[PieceKind.HEN].rect == (100, 0, 100, 100)
    assert sprites[PieceKind.LION].rect == (200, 0, 100, 100)
    assert sprites[PieceKind.GIRAFFE].rect == (300, 0, 100, 100)
    assert sprites[PieceKind.ELEPHANT].rect == (400, 0, 100, 100)


def test_piece_draw_falls_back_to_text_without_sprite_map() -> None:
    class FakeRenderedText:
        @staticmethod
        def get_rect(**kwargs):
            return kwargs

    class FakeFont:
        @staticmethod
        def render(text, antialias, color):
            assert text == "L"
            assert antialias is True
            assert color == (34, 34, 34)
            return FakeRenderedText()

    class FakeScreen:
        def __init__(self):
            self.blit_calls = []

        def blit(self, rendered, rect):
            self.blit_calls.append((rendered, rect))

    class FakeRect:
        center = (10, 20)

    screen = FakeScreen()

    _draw_piece(
        object(),
        screen,
        {"piece": FakeFont()},
        Piece(Player.BLACK, PieceKind.LION),
        FakeRect(),
        {},
    )

    assert len(screen.blit_calls) == 1
    assert isinstance(screen.blit_calls[0][0], FakeRenderedText)
    assert screen.blit_calls[0][1] == {"center": (10, 20)}


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
