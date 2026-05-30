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
