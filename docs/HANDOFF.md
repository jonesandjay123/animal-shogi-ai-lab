# Handoff

This repo is prepared as a scaffold for the next Codex implementation pass.

## What Exists Now

- Python package skeleton under `src/animal_shogi_ai_lab/`.
- Module boundaries for engine, agents, training, evaluation, and replay data.
- Documentation for architecture, rules, roadmap, and experiment tracking.
- Basic import tests so the scaffold can be validated immediately.

## What To Build First

1. Run the rule research phase from `docs/RULE_RESEARCH_PROMPT.md`.
2. Update and review `docs/GAME_RULES.md`.
3. Run the legacy audit phase from `docs/LEGACY_AUDIT_PROMPT.md`, if old repos are in scope.
4. Implement the core rules engine.
5. Add unit tests for every rule before adding learning code.
6. Add random-agent self-play to stress-test legal move generation.
7. Only then add heuristic/MCTS/RL agents.

## Non-Goals For The First Pass

- Do not start with neural network training.
- Do not build a polished web UI before the engine is correct.
- Do not bury game rules inside training code.
- Do not commit large checkpoints or run artifacts.

## Suggested First Codex Task

Use `docs/RULE_RESEARCH_PROMPT.md`.

The first Codex task should update the rules spec and stop. It should not implement `animal_shogi_ai_lab.engine` yet.
