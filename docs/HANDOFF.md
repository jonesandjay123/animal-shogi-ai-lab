# Handoff

This repo is prepared as a scaffold for the next Codex implementation pass.

## What Exists Now

- Python package skeleton under `src/animal_shogi_ai_lab/`.
- Module boundaries for engine, agents, training, evaluation, and replay data.
- Documentation for architecture, rules, roadmap, and experiment tracking.
- Basic import tests so the scaffold can be validated immediately.

## What To Build First

1. Implement the core rules engine.
2. Add unit tests for every rule before adding learning code.
3. Add random-agent self-play to stress-test legal move generation.
4. Only then add heuristic/MCTS/RL agents.

## Non-Goals For The First Pass

- Do not start with neural network training.
- Do not build a polished web UI before the engine is correct.
- Do not bury game rules inside training code.
- Do not commit large checkpoints or run artifacts.

## Suggested First Codex Task

Implement `animal_shogi_ai_lab.engine` with:

- 3x4 board model.
- Pieces: lion, giraffe, elephant, chick, hen.
- Legal move generation.
- Captures into hand.
- Drops from hand.
- Chick promotion and hen movement.
- Win conditions.
- Stable serialization for replays/tests.
