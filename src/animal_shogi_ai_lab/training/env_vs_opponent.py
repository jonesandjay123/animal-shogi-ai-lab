from __future__ import annotations

from typing import Any, SupportsFloat

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from animal_shogi_ai_lab.agents.random_agent import RandomAgent
from animal_shogi_ai_lab.engine import GameState, Player
from animal_shogi_ai_lab.training.adapter import (
    decode_action,
    encode_observation,
    legal_action_mask,
)


class AnimalShogiVsOpponentEnv(gym.Env):
    """Gymnasium environment for training a PPO agent against a fixed opponent.

    The learning_player policy only controls the specified side. The opponent controls
    the other side and auto-moves after each agent action.
    """

    metadata = {"render_modes": ["ansi", "human"]}

    def __init__(
        self,
        learning_player: Player = Player.BLACK,
        opponent: Any = None,
        render_mode: str | None = None,
        max_steps: int = 200,
        step_penalty: float = -0.001,
    ) -> None:
        super().__init__()
        self.learning_player = learning_player
        self.opponent = opponent or RandomAgent()
        self.render_mode = render_mode
        self.max_steps = max_steps
        self.step_penalty = step_penalty
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

        # If opponent plays BLACK, they must take the first turn
        if self.learning_player is Player.WHITE:
            if not self.state.is_terminal():
                legal_actions = self.state.legal_actions()
                opponent_action = self.opponent.select_action(self.state, legal_actions)
                self.state = self.state.apply_action(opponent_action)

        obs = encode_observation(self.state)
        info = {
            "action_mask": legal_action_mask(self.state),
            "ply": self.state.ply,
        }
        return obs, info

    def step(
        self, action_idx: int
    ) -> tuple[np.ndarray, SupportsFloat, bool, bool, dict[str, Any]]:
        # PPO agent action execution
        try:
            action = decode_action(int(action_idx))
        except ValueError:
            obs = encode_observation(self.state)
            info = {
                "action_mask": legal_action_mask(self.state),
                "ply": self.state.ply,
                "error": "decode_error",
            }
            return obs, -10.0, True, False, info

        legal_actions = self.state.legal_actions()
        if action not in legal_actions:
            obs = encode_observation(self.state)
            info = {
                "action_mask": legal_action_mask(self.state),
                "ply": self.state.ply,
                "error": "illegal_action",
            }
            return obs, -10.0, True, False, info

        self.state = self.state.apply_action(action)

        # Opponent auto-move if not terminal
        terminated = self.state.is_terminal()
        if not terminated:
            opp_legal = self.state.legal_actions()
            if opp_legal:
                opp_action = self.opponent.select_action(self.state, opp_legal)
                self.state = self.state.apply_action(opp_action)
                terminated = self.state.is_terminal()

        # Calculate reward from the perspective of the learning_player
        reward = 0.0
        if terminated:
            res = self.state.terminal_result()
            if res is not None:
                if res.winner is None:
                    reward = 0.0
                elif res.winner is self.learning_player:
                    reward = 1.0
                else:
                    reward = -1.0
        else:
            reward = self.step_penalty

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
        return legal_action_mask(self.state)

    def render(self) -> str | None:
        ascii_board = self.state.render_ascii()
        if self.render_mode == "human":
            print(ascii_board)
            return None
        return ascii_board
