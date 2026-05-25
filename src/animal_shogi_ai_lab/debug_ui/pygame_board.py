"""Minimal Pygame human self-play board for engine debugging."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from animal_shogi_ai_lab.debug_ui.assets import (
    load_piece_sprites,
    oriented_sprite,
    scale_to_fit,
)
from animal_shogi_ai_lab.engine import (
    BOARD_HEIGHT,
    BOARD_WIDTH,
    Action,
    DropAction,
    GameState,
    MoveAction,
    Piece,
    PieceKind,
    Player,
    Square,
    TerminalReason,
)

WINDOW_WIDTH = 760
WINDOW_HEIGHT = 620
STATE_SAVE_PATH = Path("debug_board_state.json")
BOARD_LEFT = 220
BOARD_TOP = 100
CELL_SIZE = 96
HAND_BUTTON_WIDTH = 84
HAND_BUTTON_HEIGHT = 42

BACKGROUND = (245, 241, 232)
BOARD_LIGHT = (236, 207, 147)
BOARD_DARK = (219, 186, 121)
GRID = (68, 55, 39)
TEXT = (34, 34, 34)
MUTED_TEXT = (100, 95, 88)
SELECTED = (82, 137, 255)
LEGAL = (86, 181, 122)
TERMINAL = (180, 65, 65)
HAND_BG = (255, 255, 255)

PIECE_LABELS = {
    PieceKind.LION: "L",
    PieceKind.GIRAFFE: "G",
    PieceKind.ELEPHANT: "E",
    PieceKind.CHICK: "C",
    PieceKind.HEN: "H",
}


@dataclass(frozen=True)
class LegalActionMaps:
    moves_by_from: dict[Square, dict[Square, MoveAction]]
    drops_by_kind: dict[PieceKind, dict[Square, DropAction]]


@dataclass(frozen=True)
class Selection:
    square: Square | None = None
    drop_kind: PieceKind | None = None


@dataclass
class DebugBoardSession:
    state: GameState
    selection: Selection
    move_log: list[str]
    history: list[GameState]
    status_message: str = ""

    @classmethod
    def initial(cls) -> DebugBoardSession:
        return cls(
            state=GameState.initial(),
            selection=Selection(),
            move_log=[],
            history=[],
            status_message="",
        )

    def reset(self) -> None:
        self.state = GameState.initial()
        self.selection = Selection()
        self.move_log.clear()
        self.history.clear()
        self.status_message = "Reset"

    def apply_action(self, action: Action) -> None:
        self.history.append(self.state)
        formatted = _format_action(self.state, action)
        self.state = self.state.apply_action(action)
        self.selection = Selection()
        self.move_log.append(formatted)
        if len(self.move_log) > 12:
            del self.move_log[:-12]
        self.status_message = formatted

    def undo(self) -> bool:
        if not self.history:
            self.status_message = "Nothing to undo"
            return False
        self.state = self.history.pop()
        self.selection = Selection()
        if self.move_log:
            self.move_log.pop()
        self.status_message = "Undo"
        return True

    def save(self, path: Path = STATE_SAVE_PATH) -> None:
        path.write_text(json.dumps(self.state.serialize(), indent=2), encoding="utf-8")
        self.selection = Selection()
        self.status_message = f"Saved {path}"

    def load(self, path: Path = STATE_SAVE_PATH) -> bool:
        if not path.exists():
            self.status_message = f"No save file: {path}"
            return False
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.state = GameState.deserialize(payload)
        self.selection = Selection()
        self.history.clear()
        self.move_log.clear()
        self.status_message = f"Loaded {path}"
        return True


def build_legal_action_maps(actions: list[Action]) -> LegalActionMaps:
    moves_by_from: dict[Square, dict[Square, MoveAction]] = {}
    drops_by_kind: dict[PieceKind, dict[Square, DropAction]] = {}
    for action in actions:
        if isinstance(action, MoveAction):
            moves_by_from.setdefault(action.from_square, {})[action.to_square] = action
        else:
            drops_by_kind.setdefault(action.piece_kind, {})[action.to_square] = action
    return LegalActionMaps(moves_by_from=moves_by_from, drops_by_kind=drops_by_kind)


def _get_scale_info(window_size: tuple[int, int]) -> tuple[int, int, int, int]:
    win_w, win_h = window_size
    target_ratio = WINDOW_WIDTH / WINDOW_HEIGHT
    curr_ratio = win_w / win_h

    if curr_ratio > target_ratio:
        # Window is wider: pillarbox
        new_h = win_h
        new_w = int(new_h * target_ratio)
        offset_x = (win_w - new_w) // 2
        offset_y = 0
    else:
        # Window is taller: letterbox
        new_w = win_w
        new_h = int(new_w / target_ratio)
        offset_x = 0
        offset_y = (win_h - new_h) // 2
    return new_w, new_h, offset_x, offset_y


def run_debug_board(model_path: str | None = None, ai_side: str = "WHITE") -> None:
    try:
        import pygame
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Pygame is not installed. Run `pip install -e \".[dev,ui]\"` first."
        ) from exc

    # Load PPO Model if requested
    model = None
    if model_path:
        try:
            from sb3_contrib import MaskablePPO
            print(f"Loading AI model from {model_path}...")
            model = MaskablePPO.load(model_path)
            print("Model loaded successfully.")
        except ImportError:
            print(
                "Warning: stable-baselines3 or sb3-contrib not installed. "
                "Running in human self-play mode."
            )
        except Exception as e:
            print(
                f"Warning: Failed to load model: {e}. "
                "Running in human self-play mode."
            )

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Animal Shogi Debug Board")
    
    # Virtual canvas/surface for 760x620 rendering
    canvas = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))

    clock = pygame.time.Clock()
    fonts = {
        "title": pygame.font.SysFont(None, 34),
        "body": pygame.font.SysFont(None, 24),
        "piece": pygame.font.SysFont(None, 42),
        "small": pygame.font.SysFont(None, 20),
    }

    session = DebugBoardSession.initial()
    sprites = load_piece_sprites(pygame)
    print(session.state.render_ascii())

    running = True
    while running:
        # Check if AI should take a turn
        if model is not None and not session.state.is_terminal():
            current_side = session.state.side_to_move.value  # "BLACK" or "WHITE"
            is_ai_turn = False
            if ai_side == "BOTH":
                is_ai_turn = True
            elif ai_side == "BLACK" and current_side == "BLACK":
                is_ai_turn = True
            elif ai_side == "WHITE" and current_side == "WHITE":
                is_ai_turn = True

            if is_ai_turn:
                # Pre-draw to show the human's last move
                _draw(
                    pygame=pygame,
                    screen=canvas,
                    fonts=fonts,
                    session=session,
                    action_maps=build_legal_action_maps(session.state.legal_actions()),
                    hand_buttons=_hand_button_rects(pygame, session.state),
                    sprites=sprites,
                )
                screen.fill((0, 0, 0))
                new_w, new_h, offset_x, offset_y = _get_scale_info(screen.get_size())
                if new_w > 0 and new_h > 0:
                    scaled_canvas = pygame.transform.smoothscale(canvas, (new_w, new_h))
                    screen.blit(scaled_canvas, (offset_x, offset_y))
                pygame.display.flip()

                # Natural delay to simulate thinking (300ms)
                pygame.time.wait(300)

                from animal_shogi_ai_lab.training import (
                    decode_action,
                    encode_observation,
                    legal_action_mask,
                )
                obs = encode_observation(session.state)
                mask = legal_action_mask(session.state)
                action_idx, _ = model.predict(obs, action_masks=mask, deterministic=True)
                action = decode_action(int(action_idx))
                _apply_debug_action(session, action)

        action_maps = build_legal_action_maps(session.state.legal_actions())
        hand_buttons = _hand_button_rects(pygame, session.state)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    session.reset()
                    print(session.state.render_ascii())
                elif event.key == pygame.K_u:
                    if session.undo():
                        print(session.state.render_ascii())
                    else:
                        print(session.status_message)
                elif event.key == pygame.K_s:
                    session.save()
                    print(session.status_message)
                elif event.key == pygame.K_l:
                    if session.load():
                        print(session.state.render_ascii())
                    else:
                        print(session.status_message)
                elif event.key == pygame.K_a:
                    print(session.state.render_ascii())
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Translate event.pos to virtual coords
                new_w, new_h, offset_x, offset_y = _get_scale_info(screen.get_size())
                px, py = event.pos
                if offset_x <= px < offset_x + new_w and offset_y <= py < offset_y + new_h:
                    virtual_x = int((px - offset_x) * WINDOW_WIDTH / new_w)
                    virtual_y = int((py - offset_y) * WINDOW_HEIGHT / new_h)
                    _handle_click(
                        pygame=pygame,
                        session=session,
                        pos=(virtual_x, virtual_y),
                        action_maps=action_maps,
                        hand_buttons=hand_buttons,
                    )

        # Draw all elements to the 760x620 canvas
        _draw(
            pygame=pygame,
            screen=canvas,
            fonts=fonts,
            session=session,
            action_maps=build_legal_action_maps(session.state.legal_actions()),
            hand_buttons=_hand_button_rects(pygame, session.state),
            sprites=sprites,
        )
        
        # Scale and blit canvas to screen with black letterbox bars
        screen.fill((0, 0, 0))
        new_w, new_h, offset_x, offset_y = _get_scale_info(screen.get_size())
        if new_w > 0 and new_h > 0:
            scaled_canvas = pygame.transform.smoothscale(canvas, (new_w, new_h))
            screen.blit(scaled_canvas, (offset_x, offset_y))
            
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def _handle_click(
    *,
    pygame,
    session: DebugBoardSession,
    pos: tuple[int, int],
    action_maps: LegalActionMaps,
    hand_buttons,
):
    state = session.state
    selection = session.selection
    if state.is_terminal():
        session.selection = Selection()
        return

    clicked_square = _square_from_pos(pos)
    
    # Deselect if clicking the same square again
    if selection.square is not None and clicked_square == selection.square:
        session.selection = Selection()
        return

    if selection.square is not None and clicked_square is not None:
        action = action_maps.moves_by_from.get(selection.square, {}).get(clicked_square)
        if action is not None:
            _apply_debug_action(session, action)
            return

    if selection.drop_kind is not None and clicked_square is not None:
        action = action_maps.drops_by_kind.get(selection.drop_kind, {}).get(clicked_square)
        if action is not None:
            _apply_debug_action(session, action)
            return

    for player, kind, rect in hand_buttons:
        if rect.collidepoint(pos):
            if player is state.side_to_move and kind in action_maps.drops_by_kind:
                # Deselect if clicking the same hand piece kind again
                if selection.drop_kind == kind:
                    session.selection = Selection()
                    return
                session.selection = Selection(drop_kind=kind)
                return
            session.selection = Selection()
            return

    if clicked_square is not None:
        piece = state.board.get(clicked_square)
        if piece is not None and clicked_square in action_maps.moves_by_from:
            session.selection = Selection(square=clicked_square)
            return

    session.selection = Selection()


def _apply_debug_action(session: DebugBoardSession, action: Action) -> None:
    session.apply_action(action)
    print()
    print(session.status_message)
    print(session.state.render_ascii())


def _draw(*, pygame, screen, fonts, session, action_maps, hand_buttons, sprites) -> None:
    screen.fill(BACKGROUND)
    _draw_header(screen, fonts, session)
    _draw_board(pygame, screen, fonts, session.state, session.selection, action_maps, sprites)
    _draw_hands(pygame, screen, fonts, session.state, hand_buttons, session.selection, sprites)
    _draw_help(screen, fonts)
    _draw_move_log(screen, fonts, session.move_log)


def _draw_header(screen, fonts, session: DebugBoardSession) -> None:
    state = session.state
    title = fonts["title"].render("Animal Shogi Debug Board", True, TEXT)
    screen.blit(title, (24, 20))
    
    if state.is_terminal():
        turn_text = "Game Over"
    else:
        turn_text = f"Turn: {state.side_to_move.value}"
    turn = fonts["body"].render(turn_text, True, TEXT)
    screen.blit(turn, (24, 58))
    
    terminal = state.terminal_result()
    if terminal is not None:
        reason_map = {
            TerminalReason.LION_CAPTURE: "Lion Captured",
            TerminalReason.SAFE_TRY: "Safe Try (Lion Promoted)",
            TerminalReason.REPETITION_DRAW: "Repetition Draw",
        }
        reason_name = reason_map.get(terminal.reason, terminal.reason.value)
        if terminal.winner is None:
            label = f"Draw ({reason_name})"
        else:
            label = f"Winner: {terminal.winner.value} ({reason_name})"
        rendered = fonts["body"].render(label, True, TERMINAL)
        screen.blit(rendered, (220, 58))
        
    if session.status_message:
        rendered = fonts["small"].render(session.status_message, True, MUTED_TEXT)
        screen.blit(rendered, (24, 84))


def _draw_board(pygame, screen, fonts, state, selection, action_maps, sprites) -> None:
    legal_targets = _selected_targets(selection, action_maps)
    for rank in reversed(range(BOARD_HEIGHT)):
        for file in range(BOARD_WIDTH):
            square = Square(file, rank)
            rect = _square_rect(pygame, square)
            color = BOARD_LIGHT if (file + rank) % 2 == 0 else BOARD_DARK
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, GRID, rect, 2)
            if square in legal_targets:
                pygame.draw.rect(screen, LEGAL, rect.inflate(-14, -14), 4)
            if square == selection.square:
                pygame.draw.rect(screen, SELECTED, rect.inflate(-8, -8), 4)
            _draw_piece(pygame, screen, fonts, state.board.get(square), rect, sprites)
            coord = fonts["small"].render(f"{file},{rank}", True, MUTED_TEXT)
            screen.blit(coord, (rect.left + 5, rect.top + 5))


def _draw_piece(pygame, screen, fonts, piece: Piece | None, rect, sprites) -> None:
    if piece is None:
        return
    sprite = sprites.get(piece.kind)
    if sprite is not None:
        oriented = oriented_sprite(pygame, sprite, piece.owner)
        scaled = scale_to_fit(pygame, oriented, int(rect.width * 0.82), int(rect.height * 0.82))
        screen.blit(scaled, scaled.get_rect(center=rect.center))
        return
    label = PIECE_LABELS[piece.kind]
    if piece.owner is Player.WHITE:
        label = label.lower()
    text = fonts["piece"].render(label, True, TEXT)
    screen.blit(text, text.get_rect(center=rect.center))


def _draw_hands(pygame, screen, fonts, state, hand_buttons, selection, sprites) -> None:
    for player, title_pos, y in [
        (Player.WHITE, (24, 102), 132),
        (Player.BLACK, (24, 362), 392),
    ]:
        title = fonts["body"].render(f"{player.value} hand", True, TEXT)
        screen.blit(title, title_pos)
        counts = state.hands[player]
        for _owner, kind, rect in (item for item in hand_buttons if item[0] is player):
            active = selection.drop_kind == kind and state.side_to_move is player
            color = SELECTED if active else HAND_BG
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, GRID, rect, 2)
            count = counts.get(kind, 0)
            sprite = sprites.get(kind)
            if sprite is not None:
                _draw_hand_sprite(pygame, screen, sprite, Piece(player, kind), rect)
                label = fonts["small"].render(f"x{count}", True, TEXT)
                screen.blit(label, (rect.right - 28, rect.bottom - 18))
            else:
                label = fonts["body"].render(f"{PIECE_LABELS[kind]} x{count}", True, TEXT)
                screen.blit(label, label.get_rect(center=rect.center))
        if all(
            counts.get(kind, 0) == 0
            for kind in (PieceKind.CHICK, PieceKind.GIRAFFE, PieceKind.ELEPHANT)
        ):
            empty = fonts["small"].render("-", True, MUTED_TEXT)
            screen.blit(empty, (24, y + 54))


def _draw_help(screen, fonts) -> None:
    lines = [
        "Click own piece: highlight moves",
        "Click hand piece: highlight drops",
        "R: reset",
        "U: undo",
        "S/L: save/load JSON",
        "A: print ASCII",
        "Esc: quit",
    ]
    for index, line in enumerate(lines):
        rendered = fonts["small"].render(line, True, MUTED_TEXT)
        screen.blit(rendered, (540, 420 + index * 24))


def _draw_hand_sprite(pygame, screen, sprite, piece: Piece, rect) -> None:
    oriented = oriented_sprite(pygame, sprite, piece.owner)
    scaled = scale_to_fit(pygame, oriented, int(rect.width * 0.64), int(rect.height * 0.72))
    screen.blit(scaled, scaled.get_rect(center=(rect.centerx - 10, rect.centery)))


def _draw_move_log(screen, fonts, move_log: list[str]) -> None:
    title = fonts["body"].render("Recent actions", True, TEXT)
    screen.blit(title, (540, 102))
    if not move_log:
        empty = fonts["small"].render("-", True, MUTED_TEXT)
        screen.blit(empty, (540, 132))
        return
    for index, action in enumerate(move_log[-8:]):
        rendered = fonts["small"].render(action, True, TEXT)
        screen.blit(rendered, (540, 132 + index * 24))


def _hand_button_rects(pygame, state: GameState):
    rects = []
    for player, y in [(Player.WHITE, 132), (Player.BLACK, 392)]:
        for index, kind in enumerate((PieceKind.CHICK, PieceKind.GIRAFFE, PieceKind.ELEPHANT)):
            rect = pygame.Rect(
                24 + index * (HAND_BUTTON_WIDTH + 10),
                y,
                HAND_BUTTON_WIDTH,
                HAND_BUTTON_HEIGHT,
            )
            rects.append((player, kind, rect))
    return rects


def _square_rect(pygame, square: Square):
    x = BOARD_LEFT + square.file * CELL_SIZE
    y = BOARD_TOP + (BOARD_HEIGHT - 1 - square.rank) * CELL_SIZE
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)


def _square_from_pos(pos: tuple[int, int]) -> Square | None:
    x, y = pos
    file = (x - BOARD_LEFT) // CELL_SIZE
    rank_from_top = (y - BOARD_TOP) // CELL_SIZE
    rank = BOARD_HEIGHT - 1 - rank_from_top
    square = Square(file, rank)
    return square if square.is_on_board() else None


def _selected_targets(selection: Selection, action_maps: LegalActionMaps) -> set[Square]:
    if selection.square is not None:
        return set(action_maps.moves_by_from.get(selection.square, {}))
    if selection.drop_kind is not None:
        return set(action_maps.drops_by_kind.get(selection.drop_kind, {}))
    return set()


def _format_action(state: GameState, action: Action) -> str:
    player_prefix = "B:" if state.side_to_move is Player.BLACK else "W:"
    if isinstance(action, MoveAction):
        piece = state.board.get(action.from_square)
        piece_name = piece.kind.name if piece else "PIECE"
        target_piece = state.board.get(action.to_square)
        op = "x" if target_piece else "-"
        return (
            f"{player_prefix} {piece_name} "
            f"{action.from_square.file},{action.from_square.rank}{op}"
            f"{action.to_square.file},{action.to_square.rank}"
        )
    kind = action.piece_kind.name
    file = action.to_square.file
    rank = action.to_square.rank
    return f"{player_prefix} Drop {kind}*{file},{rank}"


__all__ = ["DebugBoardSession", "build_legal_action_maps", "run_debug_board"]
