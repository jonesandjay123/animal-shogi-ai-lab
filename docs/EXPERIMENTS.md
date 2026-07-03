# Experiments

Use `experiments/` for human-readable experiment notes. Use `runs/` for generated outputs, but do not commit `runs/`.

Recommended experiment note format:

```text
Date:
Commit:
Config:
Seed:
Agent A:
Agent B:
Games:
Result:
Notes:
```

Keep experiments small until the engine is well tested.

## Recorded Runs

### 2026-05-30: `v3_black_5m_vs_heuristic_baseline`

```text
Date: 2026-05-30
Commit: c17b134 Add heuristic opponent training pipeline
Config:
  algorithm: MaskablePPO
  env: AnimalShogiVsOpponentEnv
  opponent: HeuristicAgent
  learning side: BLACK
  timesteps: 5,000,000
  n_envs: 4
  seed: 0
  step_penalty: -0.0001
Final model:
  checkpoints/animal_shogi_maskable_ppo_vs_heuristic/maskable_ppo_vs_heuristic_black_20260530_095018/final_model.zip
Result:
  Training completed at 5,000,000 steps.
Smoke evaluation:
  model: ppo_maskable_3900000_steps.zip
  opponent: RandomAgent
  model side: BLACK
  games: 50
  model wins: 36
  random wins: 13
  draws: 1
  win rate: 72.00%
  invalid actions: 0
  average length: 12.26 plies
Notes:
  First useful RL baseline after avoiding single-policy self-play collusion.
  Human playtest impression: visible improvement and basic tactical behavior.
  Final 5M model still needs formal evaluation against random and heuristic.
```

### 2026-07-03: Local baseline re-measurement (vs-random 5M model)

```text
Date: 2026-07-03
Commit: (heuristic evaluation support added the same day)
Model: checkpoints/animal_shogi_maskable_ppo_vs_random/maskable_ppo_vs_random_black_20260525_140008/final_model.zip
Note: the 5M vs-heuristic baseline referenced in docs/HANDOFF.md is NOT present
      on this machine; the vs-random model above is the only local model.

Eval 1: opponent=random, side=BLACK, games=100
  model wins: 100, opponent wins: 0, draws: 0
  win rate: 100.00%, invalid actions: 0, average length: 5.44 plies

Eval 2: opponent=heuristic, side=BLACK, games=100
  model wins: 0, opponent wins: 100, draws: 0
  win rate: 0.00%, invalid actions: 0, average length: 8.00 plies

Conclusion: the vs-random model fully dominates random play but cannot beat the
one-ply heuristic at all. Next run targets the heuristic weakness.
```

### 2026-07-03: `v4_black_pool_gpu_fresh256` (prepared; run via scripts/run_pool_training.ps1)

```text
Date: 2026-07-03
Config:
  algorithm: MaskablePPO, fresh start, net_arch [256, 256], device cuda (RTX 5080)
  env: AnimalShogiVsOpponentEnv + OpponentPoolAgent (SubprocVecEnv)
  opponent pool: heuristic 0.5 / frozen vs-random 5M model 0.25 / random 0.25
  learning side: BLACK
  timesteps: 18,000,000 target, max_minutes 80 (time-budget stop)
  n_envs: 24 (benchmarked: ~4,000 FPS; 8 dummy=1,451 / 16 dummy=1,725 / 16 subproc=3,232)
  batch_size: 1024, n_steps: 2048
  seed: 0
  step_penalty: -0.0001
Command: powershell -ExecutionPolicy Bypass -File scripts\run_pool_training.ps1
Result: (fill in after the run)
  opponent=heuristic side=BLACK games=200: ____
  opponent=random    side=BLACK games=100: ____
Notes: (fill in)
```

## Next Experiment

Run Phase 9D evaluation before more training:

```bash
animal-shogi-lab evaluate-model \
  --model checkpoints/animal_shogi_maskable_ppo_vs_heuristic/maskable_ppo_vs_heuristic_black_20260530_095018/final_model.zip \
  --games 200 \
  --side BLACK \
  --opponent random
```

After adding heuristic evaluation support, also run:

```bash
animal-shogi-lab evaluate-model \
  --model checkpoints/animal_shogi_maskable_ppo_vs_heuristic/maskable_ppo_vs_heuristic_black_20260530_095018/final_model.zip \
  --games 200 \
  --side BLACK \
  --opponent heuristic
```
