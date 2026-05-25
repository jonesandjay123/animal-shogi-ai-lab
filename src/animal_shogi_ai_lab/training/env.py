from __future__ import annotations

from typing import Any, SupportsFloat

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from animal_shogi_ai_lab.engine import GameState
from animal_shogi_ai_lab.training.adapter import (
    decode_action,
    encode_observation,
    legal_action_mask,
)


class AnimalShogiEnv(gym.Env):
    """Gymnasium environment for Animal Shogi.

    Observation space is a perspective-normalized flat float32 array of shape (126,).
    Action space is a Discrete space of 132 slots.

    Rewards:
      - Win: +1.0
      - Loss: -1.0
      - Draw: 0.0
      - Step penalty: -0.001
      - Invalid/Illegal action penalty: -10.0 (and immediate episode termination)
    """

    metadata = {"render_modes": ["ansi", "human"]}

    def __init__(self, render_mode: str | None = None, max_steps: int = 200) -> None:
        super().__init__()
        self.render_mode = render_mode
        self.max_steps = max_steps
        self.state = GameState.initial()

        self.action_space = spaces.Discrete(132)
        self.observation_space = spaces.Box(
            low=0.0,
            high=10.0,
            shape=(126,),
            dtype=np.float32,
        )

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        self.state = GameState.initial()

        obs = encode_observation(self.state)
        info = {
            "action_mask": legal_action_mask(self.state),
            "ply": self.state.ply,
        }
        return obs, info

    def step(
        self, action_idx: int
    ) -> tuple[np.ndarray, SupportsFloat, bool, bool, dict[str, Any]]:
        # Handle index parsing
        try:
            # Gym can pass numpy integers
            action = decode_action(int(action_idx))
        except ValueError:
            obs = encode_observation(self.state)
            info = {
                "action_mask": legal_action_mask(self.state),
                "ply": self.state.ply,
                "error": "decode_error",
            }
            return obs, -10.0, True, False, info

        # Verify action is legal
        legal_actions = self.state.legal_actions()
        if action not in legal_actions:
            obs = encode_observation(self.state)
            info = {
                "action_mask": legal_action_mask(self.state),
                "ply": self.state.ply,
                "error": "illegal_action",
            }
            return obs, -10.0, True, False, info

        current_player = self.state.side_to_move
        next_state = self.state.apply_action(action)
        self.state = next_state

        # Calculate reward
        terminated = self.state.is_terminal()
        reward = 0.0
        if terminated:
            res = self.state.terminal_result()
            if res is not None:
                if res.winner is None:
                    reward = 0.0
                elif res.winner is current_player:
                    reward = 1.0
                else:
                    reward = -1.0
        else:
            reward = -0.001  # Small step penalty

        truncated = False
        if not terminated and self.state.ply >= self.max_steps:
            truncated = True

        obs = encode_observation(self.state)
        info = {
            "action_mask": legal_action_mask(self.state),
            "ply": self.state.ply,
        }
        if terminated and self.state.terminal_result() is not None:
            info["terminal_reason"] = self.state.terminal_result().reason.value

        return obs, reward, terminated, truncated, info

    def action_masks(self) -> np.ndarray:
        """Returns the legal action mask for the current state."""
        return legal_action_mask(self.state)

    def render(self) -> str | None:
        ascii_board = self.state.render_ascii()
        if self.render_mode == "human":
            print(ascii_board)
            return None
        return ascii_board
