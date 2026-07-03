from __future__ import annotations

import random
from collections.abc import Sequence
from typing import Any

from animal_shogi_ai_lab.engine import Action, GameState


class OpponentPoolAgent:
    """Samples one opponent from a weighted pool at the start of each episode.

    Episode boundaries are detected from the ply counter: within a game the
    ply strictly increases between calls, so a non-increasing ply means the
    environment was reset. Each env instance should own its own pool agent.
    """

    def __init__(self, opponents: Sequence[tuple[Any, float]]) -> None:
        candidates = [(agent, weight) for agent, weight in opponents if weight > 0.0]
        if not candidates:
            raise ValueError("Opponent pool needs at least one opponent with weight > 0.")
        self._agents = [agent for agent, _ in candidates]
        self._weights = [weight for _, weight in candidates]
        self._current: Any = None
        self._last_ply = -1

    def select_action(self, state: GameState, legal_actions: Sequence[Action]) -> Action:
        if self._current is None or state.ply <= self._last_ply:
            self._current = random.choices(self._agents, weights=self._weights, k=1)[0]
        self._last_ply = state.ply
        return self._current.select_action(state, legal_actions)


__all__ = ["OpponentPoolAgent"]
