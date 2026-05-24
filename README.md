# Animal Shogi AI Lab

Research lab for building an Animal Shogi engine, agents, and self-play training pipeline.

This repository is intentionally scaffold-first. The current goal is to give GPT/Codex a clean handoff point: clear module boundaries, documented design assumptions, and a place for experiments without mixing game rules, model code, and UI prototypes.

## Goals

- Implement a correct Animal Shogi rules engine.
- Build baseline agents before reinforcement learning.
- Add self-play training and evaluation loops.
- Keep experiment outputs reproducible and easy to compare.
- Leave room for a small playable UI/demo after the engine is stable.

## Repository Layout

```text
.
├── configs/                 # Experiment and training configuration files
├── docs/                    # Architecture notes, rules, roadmap, handoff docs
├── experiments/             # Lightweight experiment notes and run logs
├── scripts/                 # CLI entrypoints and local workflow helpers
├── src/animal_shogi_ai_lab/ # Python package: engine, agents, training, eval
├── tests/                   # Pytest test suite
└── web/                     # Future web UI/demo workspace
```

## Initial Engineering Direction

Use Python for the core engine and RL pipeline. Python keeps the training stack close to common ML/RL tools while still being simple enough for early rule validation.

The first implementation milestone should not be RL. It should be a deterministic rules engine with exhaustive unit tests for legal moves, captures, drops, promotion, win conditions, and game serialization.

Recommended sequence:

1. Build the rules engine and board representation.
2. Add random and heuristic agents.
3. Add a CLI self-play loop and replay format.
4. Add Monte Carlo / MCTS-style baselines.
5. Add RL training after the engine and evaluation harness are trustworthy.
6. Add a browser UI/demo once game state serialization is stable.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Current Status

Scaffold only. Core game logic is intentionally not implemented yet.

## Handoff Notes

Start with `docs/HANDOFF.md`, then `docs/ARCHITECTURE.md` and `docs/GAME_RULES.md`.
