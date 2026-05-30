# Roadmap

## Current Position

Completed:

- Rule research and authoritative rules spec.
- Legacy audit.
- Clean rules engine and hardening tests.
- ASCII render and Pygame debug board.
- Random and heuristic agents.
- Gymnasium adapters and MaskablePPO training.
- First useful RL baseline: `v3_black_5m_vs_heuristic_baseline`.

Immediate next phase:

- Phase 9D: evaluation and model inspection. See `docs/NEXT_TRAINING_STEPS.md`.

Do not launch another long training run until the 5M baseline has been evaluated against random and heuristic opponents.

## Milestone 0: Scaffold

- Repo layout.
- Python package shell.
- Documentation.
- Import tests.

## Milestone 1: Correct Engine

- Board and coordinate system.
- Pieces and players.
- Legal moves.
- Captures and drops.
- Promotion.
- Terminal states.
- Serialization.
- Full unit tests.

## Milestone 2: Baseline Agents

- Random legal agent.
- Simple material/position heuristic agent.
- CLI match runner.
- Replay output.

## Milestone 3: Search

- Minimax or alpha-beta baseline.
- MCTS baseline.
- Evaluation against random/heuristic agents.

## Milestone 4: RL Sandbox

- Gymnasium-like environment adapter.
- Self-play data collection.
- Small policy/value model.
- Checkpointing and evaluation reports.

Current RL status:

- Single-policy alternating self-play is known bad because it learned collusive fast endings.
- `AnimalShogiVsOpponentEnv` is the recommended training environment.
- `train-maskable-ppo-vs-heuristic` produced the current baseline.
- Next work: opponent-aware evaluation, checkpoint comparison, replay samples, and then reward shaping only if the evaluation justifies it.

## Milestone 5: UI / Demo

- Playable board using engine serialization.
- Human vs random/heuristic/search/RL agents.
- Replay viewer.
