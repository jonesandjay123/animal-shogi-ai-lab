# Handoff

This repo is now past scaffold, rules research, legacy audit, clean engine, UI debug board, and the first useful RL training run.

> **2026-07-03 update:** the 5M vs-heuristic checkpoint described below is not present on the
> current machine (checkpoints are not versioned); only the 5M vs-random model exists locally.
> Heuristic evaluation support and an opponent-pool training pipeline (GPU-ready: net_arch,
> device, batch_size, time-budget stop, SubprocVecEnv) were added, and the local model was
> re-baselined: 100% vs random, 0% vs heuristic. The user runs training himself via
> `scripts/run_pool_training.ps1`. See `docs/NEXT_TRAINING_PLAN_ZH_TW.md` for the current plan.

## Current Status

- Rules spec: `docs/GAME_RULES.md` is the authority.
- Engine: pure Python rules engine under `src/animal_shogi_ai_lab/engine/`.
- Tests: focused unit coverage for engine, debug UI helpers, RL adapter, and training entry points.
- Debug UI: Pygame board with animal sprite assets, undo, save/load, ASCII print, and optional model play.
- Training: Gymnasium adapters and MaskablePPO entry points are implemented.
- Latest recommended model baseline: `v3_black_5m_vs_heuristic_baseline`.

## Latest RL Baseline

Training run:

```text
Command:
animal-shogi-lab train-maskable-ppo-vs-heuristic \
  --side BLACK \
  --timesteps 5000000 \
  --n-envs 4 \
  --seed 0 \
  --step-penalty -0.0001

Checkpoint directory:
checkpoints/animal_shogi_maskable_ppo_vs_heuristic/maskable_ppo_vs_heuristic_black_20260530_095018

Final model:
checkpoints/animal_shogi_maskable_ppo_vs_heuristic/maskable_ppo_vs_heuristic_black_20260530_095018/final_model.zip
```

The run completed at 5,000,000 steps. A 3.9M checkpoint smoke evaluation against random produced:

```text
Games: 50
Model side: BLACK
Opponent: random
Model wins: 36
Random wins: 13
Draws: 1
Invalid actions: 0
Win rate: 72.00%
Average length: 12.26 plies
```

The human playtest impression was that the model shows visible improvement and plays around a rough beginner/intermediate debug baseline level.

## What To Do Next

Do **Phase 9D: Evaluation and Model Inspection** before launching another long training run.

Priority order:

1. Add evaluation against `HeuristicAgent`, not only `RandomAgent`.
2. Evaluate `final_model.zip` against random and heuristic as BLACK, WHITE, and BOTH.
3. Compare checkpoints at 1M, 2M, 3M, 4M, and 5M to detect plateau or regression.
4. Add replay logging for selected evaluation games as JSON and/or ASCII.
5. Improve debug-board model inspection: last AI move, terminal reason, and move log clarity.
6. Only after inspection, decide whether Phase 9E should add reward shaping or a stronger opponent.

See `docs/NEXT_TRAINING_STEPS.md` for a concrete implementation plan.

## Guardrails

- Do not return to single-policy self-play where one PPO controls both BLACK and WHITE.
- Do not add complex reward shaping before measuring the current 5M baseline.
- Do not commit generated checkpoints, `runs/`, or large training artifacts.
- Keep rule behavior in `engine/`; UI, agents, and training code must use `GameState.legal_actions()` and `GameState.apply_action()`.
- Preserve action-mask compatibility for MaskablePPO.

## Verification Gate

Before committing code changes:

```bash
source .venv/bin/activate
python3 -m ruff check src tests
python3 -m compileall src
python3 -m pytest
```
