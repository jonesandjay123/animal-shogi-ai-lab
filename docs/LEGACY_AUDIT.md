# Legacy Audit

Status: Audit complete / Do not port code directly

This audit compares two legacy zip archives against this repo's current
authority: `docs/GAME_RULES.md`. Legacy code is historical reference only. It
must not override the rules spec, architecture, or action/observation design.

Audited archives:

- `AnimalShogi-ReinforcementLearning-main.zip`
- `AnimalShogiAI-main.zip`

## Executive Summary

`AnimalShogi-ReinforcementLearning-main` is closer to a compact rules prototype:
one main `shogi.py` file, unit tests, simple heuristic agents, and a small web
server/static UI. It has useful test ideas and a readable board transition
model, but it mixes check/checkmate semantics into the rules and has incomplete
server-side terminal handling.

`AnimalShogiAI-main` is closer to a playable game and RL/Gym experiment:
Pygame UI, image assets, notation history, a Gym environment, PPO training
script, and a saved model artifact. It is useful for understanding UI workflows
and common RL pitfalls, but its game logic is highly coupled to UI state,
contains an invalid action-space design, and should not be used as the engine
foundation.

Recommended migration posture:

- Copy no rules code directly.
- Reuse only concepts, test scenarios, and possibly visual assets after license
  review.
- Implement the clean engine from `docs/GAME_RULES.md` first, then write
  adapters for UI and RL.

## Repository Structures

### AnimalShogi-ReinforcementLearning-main

Top-level files:

- `shogi.py`: board representation, move generation, capture, promotion,
  check-like filtering, terminal checks, repetition counting.
- `shogi_test.py`: unit tests for setup, piece movement, capture, promotion,
  demotion, check, try-like ending, hashing.
- `shogi_ai.py`: simple heuristic agents and shallow minimax helpers.
- `shogi_server.py` / `server.py`: HTTP server for static UI and move requests.
- `recording.py`: simple move/drop/promotion record strings.
- `static/`: browser UI files.
- `static/img/`: piece image assets.
- `shogi.png`: screenshot or board image.

This repo is small and rules-centric, but it uses Python 2-era idioms in places
such as `iteritems` and `assertItemsEqual`.

### AnimalShogiAI-main

Top-level files:

- `src/game.py`: Pygame game controller, board state, move execution, capture,
  promotion, terminal flags, notation history.
- `src/piece.py`: piece types, image loading, move offsets.
- `src/utils.py`: coordinate conversion, action enumeration, serialization.
- `src/animal_shogi_gym.py`: Gym `Env` wrapper.
- `src/rl_utils.py`: headless-ish game logic used by the Gym environment.
- `src/ppo_training.py`: Stable Baselines3 PPO training entrypoint.
- `src/board.py`: Pygame rendering helpers, storage areas, labels, buttons.
- `src/main.py`: UI application entrypoint.
- `src/setup.py`: custom setup-mode UI behavior.
- `src/notation_manager.py`: notation list UI state.
- `src/play_against_ai.py`: model-play script.
- `assets/`: board/piece/control images and font.
- `output/`: generated game records.
- `animal_shogi_ppo_1000000.zip`: trained model artifact that should not be
  carried into this repo.
- `requirements.txt`: `pygame`, `pygame_gui`, `gym`, `stable_baselines3`,
  `tqdm`.

This repo is more complete as a playable demo and RL experiment, but the rules,
UI, notation, and training concerns are tightly coupled.

## Playable Game vs RL / Gym

- Closer to playable game: `AnimalShogiAI-main`. It has Pygame rendering,
  click/drag style interactions, setup mode, piece assets, move highlighting,
  notation history, and UI controls.
- Closer to RL/Gym training: `AnimalShogiAI-main`. It includes a Gym `Env`,
  Stable Baselines3 PPO training, reward calculation, and saved PPO model.
- Closer to compact rules prototype: `AnimalShogi-ReinforcementLearning-main`.
  Despite its name, its useful core is the small `shogi.py` rules prototype and
  `shogi_test.py` test suite.

## Legacy File Map

| Concern | AnimalShogi-ReinforcementLearning-main | AnimalShogiAI-main |
| --- | --- | --- |
| Board constants / coordinates | `shogi.py` | `src/const.py`, `src/utils.py` |
| Initial board | `shogi.py::StartingBoard` | `src/game.py::default_board_config`, `src/rl_utils.py::default_board_config` |
| Pieces / movement | `shogi.py::_GetOffsets` | `src/piece.py::get_move_rules`, `src/utils.py::get_available_coords` |
| Game state | `shogi.py::Board`, `shogi.py::Game` | `src/game.py::Game`, `src/rl_utils.py::AnimalShogiEnvLogic` |
| Capture / hand / drop | `shogi.py::_PossibleBoardsAndPos`, bench helpers | `src/game.py::execute_move`, `src/rl_utils.py::execute_move`, `src/utils.py::get_drop_coords` |
| Promotion / demotion | `shogi.py::_DoSpecial`, `_GetPieceAfterTaking` | `src/game.py::check_if_reached_opponent_base`, `toggle_chick_to_hen`; mirrored in `src/rl_utils.py` |
| Terminal checks | `shogi.py::HasWon`, `Next`, `Game.UpdateBoard` | `src/game.py::check_if_reached_opponent_base`, `execute_move`, `check_draw_condition`; mirrored in `src/rl_utils.py` |
| Repetition / draw | `shogi.py::Game.count` | `src/game.py::board_hist`, `AUTO_STOP_TERMINATE_TURNS`; no full-position repetition rule |
| Action enumeration | `shogi.py::PossibleMoves`, `Next` | `src/utils.py::get_possible_actions`, `src/rl_utils.py::generate_possible_actions` |
| Observation / serialization | `Board.to_dict` | `src/utils.py::get_current_game_state`, `src/animal_shogi_gym.py::convert_observation_to_array` |
| Reward | none meaningful | `src/rl_utils.py::calculate_reward` |
| Training | heuristic `shogi_ai.py` only | `src/animal_shogi_gym.py`, `src/ppo_training.py` |
| UI | `static/`, `shogi_server.py` | `src/board.py`, `src/main.py`, assets |

## Rule Comparison

### Initial Board

Both legacy repos match the piece arrangement in `docs/GAME_RULES.md` once their
coordinate systems are mapped to Black/bottom perspective.

- `AnimalShogi-ReinforcementLearning-main`: player 1 has Elephant-Lion-Giraffe
  on its home row with Chick in front; player 2 has Giraffe-Lion-Elephant with
  Chick in front.
- `AnimalShogiAI-main`: player 1 is the lower side in the UI, with
  Elephant-Lion-Giraffe on the bottom row; player `-1` is the upper side.

Do not copy either coordinate system. The clean engine should use the
zero-based `(file, rank)` convention already documented in `GAME_RULES.md`.

### Piece Movement

Both repos implement the core piece deltas correctly after accounting for their
coordinate orientation:

- Lion: one square in any direction.
- Giraffe: orthogonal one-step movement.
- Elephant: diagonal one-step movement.
- Chick: one square forward.
- Hen/Chicken: gold-general-like movement, excluding backward diagonals.

Useful reference:

- `AnimalShogi-ReinforcementLearning-main/shogi.py::_GetOffsets`
- `AnimalShogiAI-main/src/piece.py::get_move_rules`

Risks:

- `AnimalShogi-ReinforcementLearning-main` filters all moves that leave the Lion
  in check. `GAME_RULES.md` only requires attack detection for safe-try
  resolution in the first engine pass.
- `AnimalShogiAI-main` movement is mediated through mutable piece objects and UI
  coordinates, so it is not a clean source for engine logic.

### Capture, Hand, Drop, Promotion

Mostly aligned with `GAME_RULES.md`:

- Captured pieces switch owner and go to the capturer's bench/storage.
- Captured Hen/Chicken demotes to Chick.
- Drops can go to any empty square.
- Dropped Chick does not immediately promote.
- Chick promotes only when moving into the opponent's home rank.

Important incompatibilities:

- `AnimalShogiAI-main` places captured Lions into storage before/while marking
  the game over. In the clean rules, Lion capture is terminal and Lion never
  enters hand.
- `AnimalShogi-ReinforcementLearning-main` bench positions are embedded into
  the board object. The clean engine should represent hands separately as
  per-side counts.
- `AnimalShogiAI-main` storage is an ordered list of mutable `Piece` objects.
  The clean engine should use counts by piece kind.
- Neither repo cleanly exposes `MoveAction` / `DropAction` structured actions.

### Lion Try Rule

Neither repo matches the repo spec exactly.

`AnimalShogi-ReinforcementLearning-main`:

- Treats reaching the last row as ending the opponent's next-turn generation.
- Also filters moves that leave the moving side in check.
- This indirectly resembles safe try only because unsafe Lion moves are
  disallowed everywhere, not because try is resolved explicitly after applying
  the move.

`AnimalShogiAI-main`:

- Sets `game_over` when a Lion reaches the opponent base.
- Does not test whether that Lion can be captured on the opponent's next move.
- This is incompatible with the safe-try rule in `GAME_RULES.md`.

Clean engine requirement:

- Implement try as an explicit terminal transition reason: `SAFE_TRY`.
- If a Lion reaches the opponent home rank but is capturable next move, keep the
  game non-terminal and pass turn to the opponent.

### Repetition, Draw, Terminal Conditions

`AnimalShogi-ReinforcementLearning-main`:

- Has a `Counter` over boards and declares draw on the third occurrence.
- This aligns with `GAME_RULES.md` in spirit.
- Risk: board hashing is fragile and appears to include only part of each token,
  so it should not be reused.
- Terminal victory is framed as "opponent has no next boards", which adds
  checkmate-like semantics beyond the current spec.
- The HTTP server path mutates `current_game.board` and `current_game.player`
  directly, bypassing `Game.UpdateBoard`, so terminal/draw status is not
  consistently applied in server play.

`AnimalShogiAI-main`:

- Uses `AUTO_STOP_TERMINATE_TURNS = 80` as a draw/stop condition.
- Tracks `board_hist` for notation/replay, not full-position repetition.
- Does not implement third full-position occurrence.
- Rewards and winner reporting can be confused because turn updates and
  terminal checks are interleaved with notation generation.

Clean engine requirement:

- Terminal reasons should be only `LION_CAPTURE`, `SAFE_TRY`, and
  `REPETITION_DRAW` in the first pass.
- Step caps belong in training/eval wrappers, not core engine rules.

## Action, Observation, Reward Problems

### AnimalShogi-ReinforcementLearning-main

- No fixed action index space or action mask.
- Actions are represented as resulting boards or a nested move map, making them
  awkward for replay and RL.
- Board includes bench positions inside the same dictionary as board squares.
- Hashing/serialization are not robust enough for canonical repetition keys.
- Heuristic agents in `shogi_ai.py` are Python 2-style and depend on board
  generation rather than structured actions.

Useful ideas:

- Legal move enumeration as a pure-ish function is conceptually good.
- Shallow heuristic agents can inspire future baseline agents after the engine
  API exists.

### AnimalShogiAI-main

- `spaces.Discrete(60)` is not a stable action space. The environment maps an
  sampled action with modulo `len(possible_actions)`, which makes many action
  indices aliases of the same legal move and changes semantics every state.
- No legal-action mask is exposed.
- Observation is `MultiDiscrete` over raw UI-like board/state fields, not
  perspective-normalized and not separated from UI coordinate labels.
- `step()` returns the pre-action observation rather than the post-action state.
- Reward is sparse but winner/current-player handling is unreliable; terminal
  state returns do not clearly map to winner/loser perspective.
- The environment uses mutable UI-adjacent `Piece` objects and storage lists.
- `smart_check_actions()` filters possible actions as a training hint, which
  changes the legal action set and hides valid moves from the agent.
- Training script saves checkpoints into the project root and includes a saved
  model artifact in the archive. This violates this repo's artifact guardrails.

Clean adapter requirement:

- Use engine legal actions as the only source of legal moves.
- Map structured actions to the planned `132` fixed slots.
- Emit an explicit legal-action mask.
- Return post-action observations.
- Keep reward mapping outside the engine and based on terminal reason/winner.

## Worth Referencing

Good references from `AnimalShogi-ReinforcementLearning-main`:

- Basic movement offset tables.
- Unit test scenarios for setup, piece movement, capture, Hen demotion,
  Chick promotion, direction inversion, and third repetition.
- Simple heuristic-agent concepts: random action, material count, Lion progress.
- Small browser UI shape and piece images, subject to asset/license review.

Good references from `AnimalShogiAI-main`:

- Pygame board layout ideas, storage area layout, and notation/replay UI ideas.
- Piece image set and playback/control icons, subject to asset/license review.
- A cautionary example of why RL action spaces need stable indexing and masks.
- Generated notation/output examples as rough inspiration for future replay
  readability, not as canonical notation.

## Should Be Discarded

Discard or avoid:

- Checkmate-style terminal logic as core rules.
- Any rule implementation that treats an unsafe Lion try as immediate win.
- Board representations that put hands/benches into board squares.
- Mutable UI `Piece` objects as engine state.
- Ordered hand/storage lists instead of piece counts.
- Variable legal action lists hidden behind `action_idx % len(possible_actions)`.
- Action filtering that removes legal moves for "smart" training hints.
- Reward code that depends on current-player after mutation instead of explicit
  terminal winner.
- Saved PPO model artifacts and generated output files.
- Python 2-era code style and direct server/UI state mutation patterns.

## Assets And UI Material

Possible assets to review later:

- `AnimalShogi-ReinforcementLearning-main/static/img/*.png`
- `AnimalShogiAI-main/assets/*_up.png` and `*_down.png`
- `AnimalShogiAI-main/assets/background.png`
- `AnimalShogiAI-main/assets/play_left.png`, `play_right.png`,
  `fast_left.png`, `fast_right.png`

Risks:

- The archives do not establish asset licensing. Do not commit these assets
  until license/source is reviewed.
- `AnimalShogiAI-main/assets/NotoSansTC-Bold.ttf` is large compared with the
  rest of this repo; use a normal dependency or documented font source later.
- UI should wait until engine serialization is stable.

## Clean Engine Recommendations

Implement a new engine from scratch under `src/animal_shogi_ai_lab/engine/`.
Use legacy code only as a checklist.

Recommended first engine shape:

- Frozen/copy-safe `GameState`.
- Explicit `Player`, `PieceKind`, `Piece`, `Square`, `MoveAction`,
  `DropAction`, and `TerminalResult`.
- Board as 12 squares or a mapping from `(file, rank)` to piece.
- Hands as `{Player: {CHICK, GIRAFFE, ELEPHANT} counts}`.
- Legal action generation that returns structured actions.
- `apply_action` that resolves capture, demotion, promotion, terminal capture,
  safe try, side-to-move, and repetition in one place.
- Separate attack detection helper for safe-try tests.
- Canonical state key including board, side to move, hands, and promotion state.
- Serialization targeted at tests/replay/UI, not ML tensors.

Do not implement RL adapters until the engine tests pass.

## Unit Tests To Write Next

Start with focused tests before any agent/training work:

1. Initial board matches `GAME_RULES.md` exactly.
2. Black and White forward directions are opposite.
3. Each piece's legal movement from center and edge squares.
4. Own pieces block movement/capture.
5. Opponent pieces can be captured.
6. Captured Giraffe/Elephant/Chick enter capturer hand as counts.
7. Captured Hen enters hand as Chick.
8. Lion capture is terminal and Lion never enters hand.
9. Drop from hand to every empty square, including Chick on last rank.
10. Drop cannot target occupied square or a piece not in hand.
11. Dropped Chick on promotion rank does not promote.
12. Chick promotes only after moving into opponent home rank.
13. Hen has gold-general movement for both players.
14. Safe Lion try wins.
15. Unsafe Lion try remains non-terminal and gives opponent the next move.
16. Third occurrence of the same full position is `REPETITION_DRAW`.
17. Repetition key changes when side to move changes.
18. Repetition key changes when hand contents change.
19. Terminal states produce no legal actions.
20. Serialization round trip preserves board, side, hands, and terminal result.

## Final Recommendation

Use the legacy repos as reference material, not source material. The strongest
value is the catalog of scenarios and UI/asset ideas. The strongest risk is
accidentally importing incorrect terminal semantics and unstable RL interfaces.
The next implementation pass should write tests from this audit and
`GAME_RULES.md`, then implement the smallest pure engine that satisfies them.
