"""Evaluation and benchmark workflows."""

from animal_shogi_ai_lab.eval.evaluate import evaluate_model, evaluate_random
from animal_shogi_ai_lab.eval.play import play_vs_model

__all__ = [
    "evaluate_model",
    "evaluate_random",
    "play_vs_model",
]
