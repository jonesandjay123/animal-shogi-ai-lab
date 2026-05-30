# Next Training Steps

## Summary

The next agent should not start by running another blind PPO job. The current best use of time is to evaluate and inspect the completed 5M vs-heuristic baseline, then decide what training change is justified.

Current baseline:

```text
Name: v3_black_5m_vs_heuristic_baseline
Algorithm: MaskablePPO
Environment: AnimalShogiVsOpponentEnv
Learning side: BLACK
Opponent: HeuristicAgent
Timesteps: 5,000,000
Parallel envs: 4
Seed: 0
Step penalty: -0.0001
Final model:
checkpoints/animal_shogi_maskable_ppo_vs_heuristic/maskable_ppo_vs_heuristic_black_20260530_095018/final_model.zip
```

## Why This Baseline Matters

Earlier single-policy self-play was flawed because one PPO policy controlled both sides and learned fast-ending collusive behavior. The vs-heuristic run fixed the core training setup: PPO controls one side only, and an independent opponent responds.

This 5M model is the first useful RL baseline. Treat it as the reference point for all future training changes.

## Phase 9D: Evaluation and Model Inspection

Implement this phase before Phase 9E.

### 1. Evaluate Against Heuristic

Current `evaluate-model` primarily evaluates against random play. Extend it so:

```bash
animal-shogi-lab evaluate-model \
  --model checkpoints/animal_shogi_maskable_ppo_vs_heuristic/maskable_ppo_vs_heuristic_black_20260530_095018/final_model.zip \
  --games 200 \
  --side BLACK \
  --opponent heuristic
```

works with `opponent=random` and `opponent=heuristic`.

Expected implementation points:

- Add opponent factory logic in `src/animal_shogi_ai_lab/eval/evaluate.py`.
- Reuse `RandomAgent` and `HeuristicAgent`.
- Keep model actions masked with `legal_action_mask(state)`.
- Count invalid model actions even though action masking should prevent them.
- Return a structured result dict with opponent name, side, games, wins, losses, draws, invalid actions, and average length.

### 2. Evaluate Side Sensitivity

Run the final model as:

```bash
animal-shogi-lab evaluate-model --model <final_model.zip> --games 200 --side BLACK --opponent random
animal-shogi-lab evaluate-model --model <final_model.zip> --games 200 --side WHITE --opponent random
animal-shogi-lab evaluate-model --model <final_model.zip> --games 200 --side BOTH --opponent random

animal-shogi-lab evaluate-model --model <final_model.zip> --games 200 --side BLACK --opponent heuristic
animal-shogi-lab evaluate-model --model <final_model.zip> --games 200 --side WHITE --opponent heuristic
animal-shogi-lab evaluate-model --model <final_model.zip> --games 200 --side BOTH --opponent heuristic
```

Record results in `docs/EXPERIMENTS.md`.

### 3. Checkpoint Comparison

Compare training checkpoints to see whether 5M was better than earlier snapshots or whether performance plateaued.

Recommended checkpoints:

```text
ppo_maskable_1000000_steps.zip
ppo_maskable_2000000_steps.zip
ppo_maskable_3000000_steps.zip
ppo_maskable_4000000_steps.zip
ppo_maskable_5000000_steps.zip
final_model.zip
```

Use 100-200 games per checkpoint against random first. Then evaluate promising checkpoints against heuristic.

### 4. Replay Samples

Add a lightweight replay logging option for evaluation:

```bash
animal-shogi-lab evaluate-model \
  --model <model.zip> \
  --games 20 \
  --side BLACK \
  --opponent heuristic \
  --save-replays artifacts/eval_samples/v3_black_5m_vs_heuristic
```

Suggested replay format:

- JSON list of actions and terminal result.
- Optional ASCII board snapshots for a few selected games.
- Do not commit generated replay artifacts unless intentionally small and curated.

### 5. Debug Board Inspection

Use the Pygame board for human review:

```bash
animal-shogi-lab debug-board \
  --model checkpoints/animal_shogi_maskable_ppo_vs_heuristic/maskable_ppo_vs_heuristic_black_20260530_095018/final_model.zip \
  --ai-side BLACK
```

Useful UI improvements before more training:

- Highlight last AI move.
- Show model side and model path.
- Show terminal reason more prominently.
- Show a compact recent action log with model/human labels.

## Phase 9E: Possible Training Improvements

Only start this after Phase 9D identifies real weaknesses.

Candidate improvements:

- Add shaped rewards in a small, measured way.
- Train BLACK and WHITE separately if side asymmetry appears.
- Train against a stronger heuristic or mixed opponent pool.
- Add curriculum: random -> heuristic -> mixed heuristic/random.
- Add model-vs-model checkpoint evaluation.

Reward shaping should remain small compared with terminal win/loss:

```text
win/loss/draw: +1 / -1 / 0
material delta: small
Lion safety: small but important
promotion/capture: small
step penalty: keep around -0.0001 unless evidence says otherwise
```

Avoid rewarding fast endings directly. The project already observed that strong step pressure can encourage degenerate fast-loss or collusive behavior in the wrong setup.

## Suggested Next Prompt

```text
Please implement Phase 9D evaluation and model inspection.

Read docs/HANDOFF.md, docs/RL_TRAINING_NOTES.md, and docs/NEXT_TRAINING_STEPS.md.

Goals:
1. Extend evaluate-model to support opponent=random and opponent=heuristic.
2. Add checkpoint comparison helper or CLI command for selected checkpoints.
3. Add optional lightweight replay logging for evaluation games.
4. Update docs/EXPERIMENTS.md with commands and results.
5. Do not start another long training run yet.

Run:
source .venv/bin/activate && python3 -m ruff check src tests
source .venv/bin/activate && python3 -m compileall src
source .venv/bin/activate && python3 -m pytest
```
