"""Minimal Pygame human self-play board for engine debugging."""

from __future__ import annotations

from dataclasses import dataclass

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
)

WINDOW_WIDTH = 760
WINDOW_HEIGHT = 620
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


def build_legal_action_maps(actions: list[Action]) -> LegalActionMaps:
    moves_by_from: dict[Square, dict[Square, MoveAction]] = {}
    drops_by_kind: dict[PieceKind, dict[Square, DropAction]] = {}
    for action in actions:
        if isinstance(action, MoveAction):
            moves_by_from.setdefault(action.from_square, {})[action.to_square] = action
        else:
            drops_by_kind.setdefault(action.piece_kind, {})[action.to_square] = action
    return LegalActionMaps(moves_by_from=moves_by_from, drops_by_kind=drops_by_kind)


def run_debug_board() -> None:
    try:
        import pygame
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Pygame is not installed. Run `pip install -e \".[dev,ui]\"` first."
        ) from exc

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Animal Shogi Debug Board")
    clock = pygame.time.Clock()
    fonts = {
        "title": pygame.font.SysFont(None, 34),
        "body": pygame.font.SysFont(None, 24),
        "piece": pygame.font.SysFont(None, 42),
        "small": pygame.font.SysFont(None, 20),
    }

    state = GameState.initial()
    selection = Selection()
    move_log: list[str] = []
    print(state.render_ascii())

    running = True
    while running:
        action_maps = build_legal_action_maps(state.legal_actions())
        hand_buttons = _hand_button_rects(pygame, state)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    state = GameState.initial()
                    selection = Selection()
                    move_log.clear()
                    print(state.render_ascii())
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                state, selection = _handle_click(
                    pygame=pygame,
                    state=state,
                    selection=selection,
                    pos=event.pos,
                    action_maps=action_maps,
                    hand_buttons=hand_buttons,
                    move_log=move_log,
                )

        _draw(
            pygame=pygame,
            screen=screen,
            fonts=fonts,
            state=state,
            selection=selection,
            action_maps=build_legal_action_maps(state.legal_actions()),
            hand_buttons=_hand_button_rects(pygame, state),
            move_log=move_log,
        )
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def _handle_click(
    *,
    pygame,
    state: GameState,
    selection: Selection,
    pos: tuple[int, int],
    action_maps: LegalActionMaps,
    hand_buttons,
    move_log: list[str],
) -> tuple[GameState, Selection]:
    if state.is_terminal():
        return state, Selection()

    clicked_square = _square_from_pos(pos)
    if selection.square is not None and clicked_square is not None:
        action = action_maps.moves_by_from.get(selection.square, {}).get(clicked_square)
        if action is not None:
            return _apply_debug_action(state, action, move_log), Selection()

    if selection.drop_kind is not None and clicked_square is not None:
        action = action_maps.drops_by_kind.get(selection.drop_kind, {}).get(clicked_square)
        if action is not None:
            return _apply_debug_action(state, action, move_log), Selection()

    for player, kind, rect in hand_buttons:
        if rect.collidepoint(pos):
            if player is state.side_to_move and kind in action_maps.drops_by_kind:
                return state, Selection(drop_kind=kind)
            return state, Selection()

    if clicked_square is not None:
        piece = state.board.get(clicked_square)
        if piece is not None and clicked_square in action_maps.moves_by_from:
            return state, Selection(square=clicked_square)

    return state, Selection()


def _apply_debug_action(state: GameState, action: Action, move_log: list[str]) -> GameState:
    next_state = state.apply_action(action)
    move_log.append(_format_action(action))
    if len(move_log) > 8:
        del move_log[:-8]
    print()
    print(_format_action(action))
    print(next_state.render_ascii())
    return next_state


def _draw(*, pygame, screen, fonts, state, selection, action_maps, hand_buttons, move_log) -> None:
    screen.fill(BACKGROUND)
    _draw_header(screen, fonts, state)
    _draw_board(pygame, screen, fonts, state, selection, action_maps)
    _draw_hands(pygame, screen, fonts, state, hand_buttons, selection)
    _draw_help(screen, fonts)
    _draw_move_log(screen, fonts, move_log)


def _draw_header(screen, fonts, state: GameState) -> None:
    title = fonts["title"].render("Animal Shogi Debug Board", True, TEXT)
    screen.blit(title, (24, 20))
    turn = fonts["body"].render(f"Turn: {state.side_to_move.value}", True, TEXT)
    screen.blit(turn, (24, 58))
    terminal = state.terminal_result()
    if terminal is not None:
        winner = "DRAW" if terminal.winner is None else terminal.winner.value
        label = f"Terminal: {terminal.reason.value} winner={winner}"
        rendered = fonts["body"].render(label, True, TERMINAL)
        screen.blit(rendered, (220, 58))


def _draw_board(pygame, screen, fonts, state, selection, action_maps) -> None:
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
            _draw_piece(screen, fonts, state.board.get(square), rect)
            coord = fonts["small"].render(f"{file},{rank}", True, MUTED_TEXT)
            screen.blit(coord, (rect.left + 5, rect.top + 5))


def _draw_piece(screen, fonts, piece: Piece | None, rect) -> None:
    if piece is None:
        return
    label = PIECE_LABELS[piece.kind]
    if piece.owner is Player.WHITE:
        label = label.lower()
    text = fonts["piece"].render(label, True, TEXT)
    screen.blit(text, text.get_rect(center=rect.center))


def _draw_hands(pygame, screen, fonts, state, hand_buttons, selection) -> None:
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
        "Esc: quit",
    ]
    for index, line in enumerate(lines):
        rendered = fonts["small"].render(line, True, MUTED_TEXT)
        screen.blit(rendered, (540, 420 + index * 24))


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


def _format_action(action: Action) -> str:
    if isinstance(action, MoveAction):
        return (
            f"move {action.from_square.file},{action.from_square.rank}"
            f" -> {action.to_square.file},{action.to_square.rank}"
        )
    return f"drop {PIECE_LABELS[action.piece_kind]}*{action.to_square.file},{action.to_square.rank}"


__all__ = ["build_legal_action_maps", "run_debug_board"]
