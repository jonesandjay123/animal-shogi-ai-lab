# AGENTS.md

This repo is an Animal Shogi AI research lab. Keep the work staged and testable.

## Priorities

1. Research and finalize the rules spec before implementing the engine.
2. Implement a correct rules engine before training.
3. Add focused unit tests for every rule and edge case.
4. Build simple baseline agents before neural/RL agents.
5. Keep generated run outputs, checkpoints, and large artifacts out of git.
6. Preserve docs when design decisions change.

## Module Boundaries

- `src/animal_shogi_ai_lab/engine/`: pure rules, game state, actions, terminal checks, serialization.
- `src/animal_shogi_ai_lab/agents/`: policies that choose legal actions.
- `src/animal_shogi_ai_lab/training/`: self-play, RL environments, model training.
- `src/animal_shogi_ai_lab/eval/`: benchmark matches, reports, ratings.
- `src/animal_shogi_ai_lab/replay/`: replay formats and loaders.
- `web/`: future UI/demo only after engine serialization is stable.

## Guardrails

- For the first rules pass, follow `docs/RULE_RESEARCH_PROMPT.md` and stop after updating docs.
- Inspect legacy repos only after the rules spec is reviewed; use `docs/LEGACY_AUDIT_PROMPT.md`.
- Do not hide game rules inside model/training code.
- Do not start with a polished UI before the engine is correct.
- Do not commit large model files, checkpoints, or generated `runs/`.
- If a rule variant is ambiguous, document the chosen variant in `docs/GAME_RULES.md` and cover it with tests.

## Verification

Prefer small gates:

```bash
python3 -m compileall src
pytest
```
