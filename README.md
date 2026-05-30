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
python3 -m compileall src
python3 -m pytest
```

Run the verification commands from an activated virtual environment so the
project's dev dependencies, including `pytest`, are available.

## Debug Board

The Pygame debug board is a human self-play tool for validating the engine. It
does not implement game rules itself; all legal moves and drops come from the
engine API.

```bash
source .venv/bin/activate
pip install -e ".[dev,ui]"
animal-shogi-lab debug-board
```

The board uses animal sprites from
`assets/pieces/animal_pieces_sprite_sheet.png` when available. The sprite sheet
is sliced left-to-right as Chick, Hen, Lion, Giraffe, Elephant. If the image is
missing or cannot be loaded, the debug board falls back to text labels.

Controls:

- Click one of the side-to-move's board pieces to highlight legal moves.
- Click one of the side-to-move's hand pieces to highlight legal drops.
- Press `R` to reset.
- Press `U` to undo one action.
- Press `S` to save the current state to `debug_board_state.json`.
- Press `L` to load `debug_board_state.json`.
- Press `A` to print the ASCII board to the terminal.
- Press `Esc` or close the window to quit.

Each successful action also prints `GameState.render_ascii()` to the terminal.

## Reinforcement Learning & Training

This repository supports reinforcement learning training using stable-baselines3 and sb3-contrib (MaskablePPO).

### Installation

Install the reinforcement learning extra dependencies:
```bash
source .venv/bin/activate
pip install -e ".[dev,ui,rl]"
```

### Training

1. **PPO Smoke Test (Baseline)**:
   A lightweight PPO agent training script that does not use action masking (mostly used for pipeline sanity checks).
   ```bash
   animal-shogi-lab train-ppo --timesteps 1000
   ```

2. **Maskable PPO (Recommended)**:
   A PPO agent that leverages action masks to restrict predictions to legal actions.
   ```bash
   animal-shogi-lab train-maskable-ppo --timesteps 100000 --n-envs 8 --seed 0
   ```
   *Note: Animal Shogi's environment stepping is CPU-bound. Adjusting `--n-envs` allows parallel execution to maximize CPU utilization, which is key to feed the GPU efficiently.*

3. **Maskable PPO vs Heuristic Opponent (Current recommended next run)**:
   A single-side PPO agent trained against a fixed one-ply heuristic opponent. This avoids
   the earlier single-policy self-play failure mode where one policy controlled both sides.
   ```bash
   animal-shogi-lab train-maskable-ppo-vs-heuristic \
     --side BLACK \
     --timesteps 1000000 \
     --n-envs 4 \
     --seed 0 \
     --step-penalty -0.0001
   ```

Training runs save checkpoints, log config parameters, and store tensorboard runs under the ignored `checkpoints/` and `runs/` directories.

### Evaluation

1. **Random vs Random Baseline**:
   ```bash
   animal-shogi-lab evaluate-random --games 100
   ```

2. **Model vs Random Agent**:
   Evaluates a trained model against a random agent, alternating Black/White roles.
   ```bash
   animal-shogi-lab evaluate-model --model checkpoints/animal_shogi_maskable_ppo/maskable_ppo_xxxxxx/final_model.zip --games 100
   ```

## Current Status

Clean rules engine MVP, agents, Gymnasium adapters, and MaskablePPO training pipelines are fully implemented and verified by tests.

## Handoff Notes

Start with `docs/HANDOFF.md`, then `docs/RULE_RESEARCH_PROMPT.md`.

Recommended phase order:

1. Rule research and `docs/GAME_RULES.md` update.
2. Legacy repo audit using `docs/LEGACY_AUDIT_PROMPT.md`.
3. Clean engine implementation.
4. Baseline agents and evaluation.
5. RL training.
