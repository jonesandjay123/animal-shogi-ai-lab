from __future__ import annotations

import random
from collections.abc import Sequence
from typing import Any

import numpy as np

from animal_shogi_ai_lab.engine import Action, GameState, Player


class ModelOpponentAgent:
    """Wraps a frozen MaskablePPO policy so it can act as an env opponent.

    Observations from ``encode_observation`` are perspective-normalized, but
    action encoding is absolute. When the wrapped model (trained as BLACK)
    plays WHITE, the legal-action mask is mirrored into the model's egocentric
    frame before prediction and the predicted action is mirrored back.
    """

    def __init__(
        self,
        model: Any = None,
        model_path: str | None = None,
        deterministic: bool = False,
    ) -> None:
        if model is None and model_path is None:
            raise ValueError("Provide either a loaded model or a model_path.")
        if model is None:
            from sb3_contrib import MaskablePPO

            model = MaskablePPO.load(model_path)
        self.model = model
        self.deterministic = deterministic

    def select_action(self, state: GameState, legal_actions: Sequence[Action]) -> Action:
        if not legal_actions:
            raise ValueError("No legal actions available.")

        from animal_shogi_ai_lab.training.adapter import (
            decode_action,
            encode_action,
            encode_observation,
            mirror_action,
        )

        obs = encode_observation(state)
        mirrored = state.side_to_move is Player.WHITE

        mask = np.zeros(132, dtype=np.bool_)
        for action in legal_actions:
            ego_action = mirror_action(action) if mirrored else action
            try:
                mask[encode_action(ego_action)] = True
            except ValueError:
                pass

        if not mask.any():
            return random.choice(list(legal_actions))

        action_idx, _ = self.model.predict(
            obs, action_masks=mask, deterministic=self.deterministic
        )
        predicted = decode_action(int(action_idx))
        if mirrored:
            predicted = mirror_action(predicted)

        if predicted not in legal_actions:
            return random.choice(list(legal_actions))
        return predicted


__all__ = ["ModelOpponentAgent"]
