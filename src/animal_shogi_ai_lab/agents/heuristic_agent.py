from __future__ import annotations

import random
from collections.abc import Sequence

from animal_shogi_ai_lab.engine import (
    Action,
    DropAction,
    GameState,
    MoveAction,
    PieceKind,
    Player,
    Square,
)

PIECE_VALUES = {
    PieceKind.LION: 1000,
    PieceKind.HEN: 5,
    PieceKind.GIRAFFE: 4,
    PieceKind.ELEPHANT: 4,
    PieceKind.CHICK: 2,
}


class HeuristicAgent:
    """A lightweight one-ply opponent for training smoke tests and baselines."""

    def select_action(self, state: GameState, legal_actions: Sequence[Action]) -> Action:
        if not legal_actions:
            raise ValueError("No legal actions available.")

        scored = [(self.score_action(state, action), action) for action in legal_actions]
        best_score = max(score for score, _ in scored)
        best_actions = [action for score, action in scored if score == best_score]
        return random.choice(best_actions)

    def score_action(self, state: GameState, action: Action) -> float:
        player = state.side_to_move
        score = 0.0

        if isinstance(action, MoveAction):
            captured = state.board.get(action.to_square)
            if captured is not None:
                score += PIECE_VALUES[captured.kind] * 10.0
            moving_piece = state.board[action.from_square]
            if (
                moving_piece.kind is PieceKind.CHICK
                and action.to_square.rank == moving_piece.owner.try_rank
            ):
                score += 8.0

        try:
            next_state = state.apply_action(action)
        except ValueError:
            return float("-inf")

        terminal = next_state.terminal_result()
        if terminal is not None:
            if terminal.winner is player:
                return 100000.0
            if terminal.winner is player.opponent:
                return -100000.0
            return 0.0

        if _lion_can_be_captured(next_state, player):
            score -= 5000.0
        if _lion_can_be_captured(next_state, player.opponent):
            score += 15.0

        score += _material_score(next_state, player) * 0.5
        score += _position_score(next_state, player)

        if isinstance(action, DropAction):
            score += 0.2

        return score


def _material_score(state: GameState, player: Player) -> int:
    score = 0
    for piece in state.board.values():
        value = PIECE_VALUES[piece.kind]
        score += value if piece.owner is player else -value
    for owner, sign in [(player, 1), (player.opponent, -1)]:
        for kind, count in state.hands[owner].items():
            score += sign * PIECE_VALUES[kind] * count
    return score


def _position_score(state: GameState, player: Player) -> float:
    score = 0.0
    for square, piece in state.board.items():
        if piece.kind is PieceKind.LION:
            continue
        advancement = _relative_rank(square, piece.owner)
        value = advancement * 0.1
        score += value if piece.owner is player else -value
    return score


def _relative_rank(square: Square, player: Player) -> int:
    return square.rank if player is Player.BLACK else 3 - square.rank


def _lion_can_be_captured(state: GameState, lion_owner: Player) -> bool:
    lion_square = next(
        (
            square
            for square, piece in state.board.items()
            if piece.owner is lion_owner and piece.kind is PieceKind.LION
        ),
        None,
    )
    if lion_square is None:
        return True

    if state.side_to_move is not lion_owner.opponent:
        return False

    return any(
        isinstance(action, MoveAction) and action.to_square == lion_square
        for action in state.legal_actions()
    )


__all__ = ["HeuristicAgent", "PIECE_VALUES"]
