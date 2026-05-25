"""Agent implementations.

Agents should choose from legal actions exposed by the engine. Keep learning
state and model-specific code outside the rules engine.
"""

from animal_shogi_ai_lab.agents.random_agent import RandomAgent, run_random_self_play

__all__ = [
    "RandomAgent",
    "run_random_self_play",
]
