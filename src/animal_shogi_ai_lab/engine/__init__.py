"""Pure Animal Shogi rules engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TypeAlias

BOARD_WIDTH = 3
BOARD_HEIGHT = 4
DROP_PIECE_KINDS: tuple[PieceKind, ...]


class Player(StrEnum):
    BLACK = "BLACK"
    WHITE = "WHITE"

    @property
    def forward(self) -> int:
        return 1 if self is Player.BLACK else -1

    @property
    def opponent(self) -> Player:
        return Player.WHITE if self is Player.BLACK else Player.BLACK

    @property
    def home_rank(self) -> int:
        return 0 if self is Player.BLACK else BOARD_HEIGHT - 1

    @property
    def try_rank(self) -> int:
        return BOARD_HEIGHT - 1 if self is Player.BLACK else 0


class PieceKind(StrEnum):
    LION = "LION"
    GIRAFFE = "GIRAFFE"
    ELEPHANT = "ELEPHANT"
    CHICK = "CHICK"
    HEN = "HEN"


DROP_PIECE_KINDS = (PieceKind.CHICK, PieceKind.GIRAFFE, PieceKind.ELEPHANT)


class TerminalReason(StrEnum):
    LION_CAPTURE = "LION_CAPTURE"
    SAFE_TRY = "SAFE_TRY"
    REPETITION_DRAW = "REPETITION_DRAW"


@dataclass(frozen=True, order=True)
class Square:
    file: int
    rank: int

    def is_on_board(self) -> bool:
        return 0 <= self.file < BOARD_WIDTH and 0 <= self.rank < BOARD_HEIGHT


Position: TypeAlias = Square


@dataclass(frozen=True)
class Piece:
    owner: Player
    kind: PieceKind


@dataclass(frozen=True)
class MoveAction:
    from_square: Square
    to_square: Square


@dataclass(frozen=True)
class DropAction:
    piece_kind: PieceKind
    to_square: Square


Action: TypeAlias = MoveAction | DropAction


@dataclass(frozen=True)
class TerminalResult:
    reason: TerminalReason
    winner: Player | None


Board: TypeAlias = dict[Square, Piece]
Hands: TypeAlias = dict[Player, dict[PieceKind, int]]
StateKey: TypeAlias = tuple[Any, ...]


_RELATIVE_DELTAS: dict[PieceKind, tuple[tuple[int, int], ...]] = {
    PieceKind.LION: (
        (-1, -1),
        (0, -1),
        (1, -1),
        (-1, 0),
        (1, 0),
        (-1, 1),
        (0, 1),
        (1, 1),
    ),
    PieceKind.GIRAFFE: ((0, -1), (-1, 0), (1, 0), (0, 1)),
    PieceKind.ELEPHANT: ((-1, -1), (1, -1), (-1, 1), (1, 1)),
    PieceKind.CHICK: ((0, 1),),
    PieceKind.HEN: ((-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1), (0, -1)),
}


def _empty_hands() -> Hands:
    return {
        Player.BLACK: {kind: 0 for kind in DROP_PIECE_KINDS},
        Player.WHITE: {kind: 0 for kind in DROP_PIECE_KINDS},
    }


def _normalize_hands(hands: Hands | None) -> Hands:
    normalized = _empty_hands()
    if not hands:
        return normalized
    for player in Player:
        for kind in DROP_PIECE_KINDS:
            normalized[player][kind] = int(hands.get(player, {}).get(kind, 0))
    return normalized


def _copy_board(board: Board) -> Board:
    return dict(board)


def _copy_hands(hands: Hands) -> Hands:
    return {player: dict(counts) for player, counts in hands.items()}


def _hand_piece_after_capture(kind: PieceKind) -> PieceKind | None:
    if kind is PieceKind.LION:
        return None
    if kind is PieceKind.HEN:
        return PieceKind.CHICK
    return kind


@dataclass(frozen=True)
class GameState:
    board: Board
    side_to_move: Player
    hands: Hands
    ply: int = 0
    _terminal_result: TerminalResult | None = None
    _repetition_counts: dict[StateKey, int] | None = None

    @classmethod
    def initial(cls) -> GameState:
        board = {
            Square(0, 0): Piece(Player.BLACK, PieceKind.ELEPHANT),
            Square(1, 0): Piece(Player.BLACK, PieceKind.LION),
            Square(2, 0): Piece(Player.BLACK, PieceKind.GIRAFFE),
            Square(1, 1): Piece(Player.BLACK, PieceKind.CHICK),
            Square(1, 2): Piece(Player.WHITE, PieceKind.CHICK),
            Square(0, 3): Piece(Player.WHITE, PieceKind.GIRAFFE),
            Square(1, 3): Piece(Player.WHITE, PieceKind.LION),
            Square(2, 3): Piece(Player.WHITE, PieceKind.ELEPHANT),
        }
        return cls.from_parts(board=board, side_to_move=Player.BLACK)

    @classmethod
    def from_parts(
        cls,
        *,
        board: Board,
        side_to_move: Player = Player.BLACK,
        hands: Hands | None = None,
        ply: int = 0,
        terminal_result: TerminalResult | None = None,
        repetition_counts: dict[StateKey, int] | None = None,
    ) -> GameState:
        normalized_board = _copy_board(board)
        normalized_hands = _normalize_hands(hands)
        state = cls(
            board=normalized_board,
            side_to_move=side_to_move,
            hands=normalized_hands,
            ply=ply,
            _terminal_result=terminal_result,
            _repetition_counts=None,
        )
        counts = (
            dict(repetition_counts)
            if repetition_counts is not None
            else {state.state_key(): 1}
        )
        return cls(
            board=normalized_board,
            side_to_move=side_to_move,
            hands=normalized_hands,
            ply=ply,
            _terminal_result=terminal_result,
            _repetition_counts=counts,
        )

    def is_terminal(self) -> bool:
        return self._terminal_result is not None

    def terminal_result(self) -> TerminalResult | None:
        return self._terminal_result

    def legal_actions(self) -> list[Action]:
        if self.is_terminal():
            return []

        actions: list[Action] = []
        for square, piece in sorted(self.board.items()):
            if piece.owner is not self.side_to_move:
                continue
            for destination in self._piece_destinations(square, piece):
                actions.append(MoveAction(square, destination))

        for kind in DROP_PIECE_KINDS:
            if self.hands[self.side_to_move].get(kind, 0) <= 0:
                continue
            for square in all_squares():
                if square not in self.board:
                    actions.append(DropAction(kind, square))

        return actions

    def apply_action(self, action: Action) -> GameState:
        if action not in self.legal_actions():
            raise ValueError(f"illegal action: {action!r}")
        if isinstance(action, MoveAction):
            return self._apply_move(action)
        return self._apply_drop(action)

    def serialize(self) -> dict[str, Any]:
        return {
            "board": [
                {
                    "file": square.file,
                    "rank": square.rank,
                    "owner": piece.owner.value,
                    "kind": piece.kind.value,
                }
                for square, piece in sorted(self.board.items())
            ],
            "hands": {
                player.value: {kind.value: self.hands[player][kind] for kind in DROP_PIECE_KINDS}
                for player in Player
            },
            "side_to_move": self.side_to_move.value,
            "ply": self.ply,
            "terminal": None
            if self._terminal_result is None
            else {
                "reason": self._terminal_result.reason.value,
                "winner": None
                if self._terminal_result.winner is None
                else self._terminal_result.winner.value,
            },
            "repetition_counts": [
                {"key": _serialize_state_key(key), "count": count}
                for key, count in sorted(
                    (self._repetition_counts or {}).items(), key=lambda item: repr(item[0])
                )
            ],
        }

    @classmethod
    def deserialize(cls, payload: dict[str, Any]) -> GameState:
        board = {}
        for item in payload["board"]:
            square = Square(item["file"], item["rank"])
            board[square] = Piece(Player(item["owner"]), PieceKind(item["kind"]))
        hands = {
            Player(player_name): {
                PieceKind(kind_name): count for kind_name, count in counts.items()
            }
            for player_name, counts in payload["hands"].items()
        }
        terminal_payload = payload.get("terminal")
        terminal = None
        if terminal_payload is not None:
            winner = terminal_payload.get("winner")
            terminal = TerminalResult(
                reason=TerminalReason(terminal_payload["reason"]),
                winner=None if winner is None else Player(winner),
            )
        repetition_counts = {
            _deserialize_state_key(item["key"]): item["count"]
            for item in payload.get("repetition_counts", [])
        }
        return cls.from_parts(
            board=board,
            side_to_move=Player(payload["side_to_move"]),
            hands=hands,
            ply=payload.get("ply", 0),
            terminal_result=terminal,
            repetition_counts=repetition_counts or None,
        )

    def state_key(self) -> StateKey:
        board_key = tuple(
            (square.file, square.rank, piece.owner.value, piece.kind.value)
            for square, piece in sorted(self.board.items())
        )
        hands_key = tuple(
            (
                player.value,
                tuple((kind.value, self.hands[player][kind]) for kind in DROP_PIECE_KINDS),
            )
            for player in Player
        )
        return (board_key, self.side_to_move.value, hands_key)

    def _piece_destinations(self, square: Square, piece: Piece) -> list[Square]:
        destinations: list[Square] = []
        for df, relative_dr in _RELATIVE_DELTAS[piece.kind]:
            candidate = Square(square.file + df, square.rank + relative_dr * piece.owner.forward)
            if not candidate.is_on_board():
                continue
            occupant = self.board.get(candidate)
            if occupant is not None and occupant.owner is piece.owner:
                continue
            destinations.append(candidate)
        return destinations

    def _apply_move(self, action: MoveAction) -> GameState:
        moving_piece = self.board[action.from_square]
        captured_piece = self.board.get(action.to_square)
        board = _copy_board(self.board)
        hands = _copy_hands(self.hands)

        del board[action.from_square]

        terminal = None
        if captured_piece is not None:
            if captured_piece.kind is PieceKind.LION:
                terminal = TerminalResult(TerminalReason.LION_CAPTURE, self.side_to_move)
            else:
                hand_kind = _hand_piece_after_capture(captured_piece.kind)
                if hand_kind is not None:
                    hands[self.side_to_move][hand_kind] += 1

        placed_piece = moving_piece
        if (
            moving_piece.kind is PieceKind.CHICK
            and action.to_square.rank == moving_piece.owner.try_rank
        ):
            placed_piece = Piece(moving_piece.owner, PieceKind.HEN)
        board[action.to_square] = placed_piece

        if terminal is None and placed_piece.kind is PieceKind.LION:
            if action.to_square.rank == placed_piece.owner.try_rank and not _lion_is_attacked(
                board, action.to_square, placed_piece.owner.opponent
            ):
                terminal = TerminalResult(TerminalReason.SAFE_TRY, self.side_to_move)

        return self._next_state(board, hands, terminal)

    def _apply_drop(self, action: DropAction) -> GameState:
        board = _copy_board(self.board)
        hands = _copy_hands(self.hands)
        hands[self.side_to_move][action.piece_kind] -= 1
        board[action.to_square] = Piece(self.side_to_move, action.piece_kind)
        return self._next_state(board, hands, None)

    def _next_state(
        self, board: Board, hands: Hands, terminal: TerminalResult | None
    ) -> GameState:
        next_side = self.side_to_move if terminal is not None else self.side_to_move.opponent
        provisional = GameState.from_parts(
            board=board,
            side_to_move=next_side,
            hands=hands,
            ply=self.ply + 1,
            terminal_result=terminal,
            repetition_counts=self._repetition_counts or {},
        )
        counts = dict(self._repetition_counts or {})
        key = provisional.state_key()
        counts[key] = counts.get(key, 0) + 1
        final_terminal = terminal
        if final_terminal is None and counts[key] >= 3:
            final_terminal = TerminalResult(TerminalReason.REPETITION_DRAW, None)
        return GameState.from_parts(
            board=board,
            side_to_move=next_side,
            hands=hands,
            ply=self.ply + 1,
            terminal_result=final_terminal,
            repetition_counts=counts,
        )


def all_squares() -> tuple[Square, ...]:
    return tuple(Square(file, rank) for rank in range(BOARD_HEIGHT) for file in range(BOARD_WIDTH))


def _lion_is_attacked(board: Board, lion_square: Square, attacker: Player) -> bool:
    for square, piece in board.items():
        if piece.owner is not attacker:
            continue
        for df, relative_dr in _RELATIVE_DELTAS[piece.kind]:
            target = Square(square.file + df, square.rank + relative_dr * piece.owner.forward)
            if target == lion_square:
                return True
    return False


def _serialize_state_key(key: StateKey) -> Any:
    return key


def _deserialize_state_key(key: Any) -> StateKey:
    board_key, side_to_move, hands_key = key
    return (
        tuple(tuple(item) for item in board_key),
        side_to_move,
        tuple(
            (player, tuple(tuple(kind_count) for kind_count in counts))
            for player, counts in hands_key
        ),
    )


__all__ = [
    "Action",
    "BOARD_HEIGHT",
    "BOARD_WIDTH",
    "DropAction",
    "GameState",
    "MoveAction",
    "Piece",
    "PieceKind",
    "Player",
    "Position",
    "Square",
    "TerminalReason",
    "TerminalResult",
    "all_squares",
]
