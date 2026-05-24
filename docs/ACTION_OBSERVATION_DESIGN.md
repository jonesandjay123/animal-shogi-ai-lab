# Action And Observation Design

Status: Draft / Depends on `docs/GAME_RULES.md`

This document is a design draft for future agents and RL adapters. It is not an
engine implementation plan by itself, and it should not introduce dependencies
from `engine/` to ML libraries.

## Design Goals

- Keep the pure engine representation readable, serializable, and easy to test.
- Expose a variable-length legal-action list from the engine.
- Add fixed action indices and observation tensors in adapters after the rules
  engine is correct.
- Make illegal-action masking explicit for policy-gradient and value-based
  agents.
- Keep replay/UI formats close to engine state, not tensor encodings.

## Engine-Level Actions

Use structured actions in `animal_shogi_ai_lab.engine`:

```text
MoveAction(from_square, to_square)
DropAction(piece_kind, to_square)
```

Where:

- `from_square` and `to_square` use zero-based `(file, rank)` coordinates.
- `piece_kind` for drops is one of `CHICK`, `GIRAFFE`, or `ELEPHANT`.
- `HEN` is not droppable because captured Hens demote to Chicks.
- `LION` is not droppable because Lion capture ends the game.

The engine should provide:

- `legal_actions(state) -> list[Action]`
- `apply_action(state, action) -> GameState`
- A clear error for applying an illegal action in debug/test contexts.

## Fixed Action Space Draft

Future RL adapters should map structured actions to a fixed index space and
emit an action mask.

Recommended compact action space:

- Board squares: `12`.
- Move directions: `8`, matching Lion-neighborhood deltas.
- Move slots: `12 * 8 = 96`.
- Drop piece kinds: `3` (`CHICK`, `GIRAFFE`, `ELEPHANT`).
- Drop slots: `3 * 12 = 36`.
- Total slots: `132`.

Move direction order should be stable:

```text
0: NW  (-1, +1 from Black board coordinates)
1: N   ( 0, +1)
2: NE  (+1, +1)
3: W   (-1,  0)
4: E   (+1,  0)
5: SW  (-1, -1)
6: S   ( 0, -1)
7: SE  (+1, -1)
```

These are board-coordinate directions, not side-relative directions. The mapper
must convert each legal structured move into the matching board delta.

Drop index layout:

```text
96 + drop_kind_index * 12 + square_index
```

Where:

- `drop_kind_index`: `0 = CHICK`, `1 = GIRAFFE`, `2 = ELEPHANT`.
- `square_index = rank * 3 + file`.

Illegal actions are represented by mask value `0`; legal actions by mask value
`1`. Policy adapters should never silently apply an illegal sampled action.

## Legal Action Mask

The action mask should be derived only from `engine.legal_actions(state)`.

Mask requirements:

- Shape: `(132,)`.
- Type: bool or integer.
- Exactly one `true` entry per legal action.
- Terminal states must produce an all-false mask.
- The mapper must be bijective for legal actions: an action maps to one index,
  and that index maps back to the same structured action for the current state.

## Engine-Level State Serialization

Before ML tensors, define a readable serialization suitable for tests, replays,
and future UI:

```text
{
  "board": [
    [{"owner": "BLACK", "kind": "ELEPHANT"}, ...],
    ...
  ],
  "hands": {
    "BLACK": {"CHICK": 0, "GIRAFFE": 0, "ELEPHANT": 0},
    "WHITE": {"CHICK": 0, "GIRAFFE": 0, "ELEPHANT": 0}
  },
  "side_to_move": "BLACK",
  "ply": 0,
  "terminal": null
}
```

The exact JSON layout can change during engine design, but it should preserve
these fields explicitly.

## Observation Encoding Draft

Use perspective-normalized tensors for ML by default. From the side to move's
perspective, "forward" should always point toward increasing tensor rank.

Recommended first tensor components:

- Board tensor: `10 x 4 x 3`.
- Planes `0..4`: own `LION`, `GIRAFFE`, `ELEPHANT`, `CHICK`, `HEN`.
- Planes `5..9`: opponent `LION`, `GIRAFFE`, `ELEPHANT`, `CHICK`, `HEN`.
- Hand features: 6 scalar counts:
  own/opponent `CHICK`, `GIRAFFE`, `ELEPHANT`.
- Optional repetition feature: scalar or small one-hot count for current full
  position occurrence.

Perspective normalization:

- If side to move is Black, keep board coordinates as documented in
  `GAME_RULES.md`.
- If side to move is White, rotate the board 180 degrees and swap own/opponent
  planes.
- Do not encode side-to-move in the normalized tensor unless a model needs to
  mix normalized and non-normalized data.

## Rewards Draft

The pure engine should expose terminal reasons, not RL rewards. RL environments
can map them as:

- Current player wins by `LION_CAPTURE`: `+1` for winner, `-1` for loser.
- Current player wins by `SAFE_TRY`: `+1` for winner, `-1` for loser.
- `REPETITION_DRAW`: `0` for both sides.
- Wrapper-level step cap draw, if used later: `0` for both sides and a separate
  result reason outside core rules.

Keep reward shaping out of the first engine implementation.

## Replay And UI Notes

Replay records should store structured actions, not fixed action indices. Fixed
indices are adapter-specific and may change.

Recommended replay event fields:

- `ply`
- `side`
- `action`
- `state_before_hash`
- `state_after_hash`
- `terminal`

Future UI should consume engine serialization and legal structured actions. It
should not need to know about ML planes or fixed action slots.

## Open Questions For Review

- Whether to expose a compact `132`-slot action space or reserve unused Lion
  drop slots for a rectangular `144`-slot table. This draft recommends `132`.
- Whether repetition count belongs in every training observation or only in
  state metadata for terminal detection.
- Whether to add a non-normalized debug tensor for easier visual comparison
  against board diagrams.
