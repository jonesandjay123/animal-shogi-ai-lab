# Animal Shogi Rules Spec

Status: Research draft / Ready for review before engine implementation

This document defines the rule set this repo should implement for Animal Shogi
/ Dobutsu Shogi / Let's Catch the Lion. It is based only on public rule
sources, not legacy code.

## Default Ruleset

The repo should implement one default ruleset named `dobutsu_shogi_standard`.
It follows the 3x4 Madoka Kitao game as described by Nekomado, the Nestor Games
English rulebook, and lishogi's Dobutsu variant page.

Where public sources differ, prefer rules that are easiest to make explicit,
test, and use in self-play:

- A player wins by capturing the opposing Lion.
- A player wins by moving their Lion to the opponent's home rank only if that
  Lion is not capturable by the opponent on the next move.
- A repeated full position for the third time is a draw.
- No maximum move count is part of the game rules. Add any training/evaluation
  step cap outside the pure engine.

## Board And Coordinates

The board is 3 columns by 4 rows. Use zero-based engine coordinates:

- `file`: integer `0..2`, left to right from Black's point of view.
- `rank`: integer `0..3`, bottom to top from Black's point of view.
- Black starts at the bottom and moves forward by `+1` rank.
- White starts at the top and moves forward by `-1` rank.

Named ranks:

- Black home rank: `rank == 0`.
- Black promotion / try rank, also White home rank: `rank == 3`.
- White home rank: `rank == 3`.
- White promotion / try rank, also Black home rank: `rank == 0`.

Coordinates are intentionally engine-native instead of matching any printed
board notation. Replay/UI adapters can add labels later after the engine API is
stable.

## Players And Directions

Use two sides:

- `BLACK`: first player / bottom side / forward delta `(0, +1)`.
- `WHITE`: second player / top side / forward delta `(0, -1)`.

All directional piece movement is relative to the owning side. For example, a
Black Chick moves from `(file, rank)` to `(file, rank + 1)`, while a White Chick
moves to `(file, rank - 1)`.

## Initial Setup

From Black's point of view:

```text
rank 3:  white Giraffe | white Lion | white Elephant
rank 2:  empty         | white Chick | empty
rank 1:  empty         | black Chick | empty
rank 0:  black Elephant| black Lion  | black Giraffe
          file 0         file 1       file 2
```

Both players start with empty hands. Chick/Hen tiles start with the Chick side
active.

## Pieces

Piece kinds:

- `LION`
- `GIRAFFE`
- `ELEPHANT`
- `CHICK`
- `HEN`, the promoted Chick

Only Chick promotes. Lion, Giraffe, Elephant, and Hen do not promote further.

## Movement

All moves are one square. A move is legal only if the destination is inside the
board and is either empty or occupied by an opponent piece.

Relative deltas are listed as `(df, dr)` where `dr == +1` is forward for the
owning side. Convert to board coordinates by multiplying `dr` by the side's
forward direction.

| Piece | Relative deltas |
| --- | --- |
| Lion | `(-1, -1)`, `(0, -1)`, `(1, -1)`, `(-1, 0)`, `(1, 0)`, `(-1, 1)`, `(0, 1)`, `(1, 1)` |
| Giraffe | `(0, -1)`, `(-1, 0)`, `(1, 0)`, `(0, 1)` |
| Elephant | `(-1, -1)`, `(1, -1)`, `(-1, 1)`, `(1, 1)` |
| Chick | `(0, 1)` |
| Hen | `(-1, 0)`, `(1, 0)`, `(-1, 1)`, `(0, 1)`, `(1, 1)`, `(0, -1)` |

Hen moves like a Shogi gold general / promoted pawn: one square forward,
forward diagonals, sideways, or straight backward, but not backward diagonals.

## Captures

If a legal move lands on an opponent piece, that piece is captured.

- Captured non-Lion pieces enter the capturer's hand.
- Capturing the opponent Lion immediately ends the game as a win for the
  capturing player.
- A captured Hen demotes and enters hand as a Chick.
- Captured pieces switch ownership to the capturing player.
- A square can contain at most one piece.

The pure engine should not require a separate "check" declaration. It only
needs attack detection for illegal Lion try wins and future test helpers.

## Hands And Drops

On a turn, a player may either move one on-board piece or drop one piece from
hand.

Drop rules for this repo:

- A dropped piece must come from the side-to-move's hand.
- A dropped piece may be placed on any empty square.
- There is no `nifu` restriction; multiple Chicks on one file are allowed.
- A Chick may be dropped on the farthest rank even though it cannot move from
  there.
- A dropped Chick does not promote immediately, including when dropped on the
  farthest rank.
- A Hen is never held or dropped. Captured Hens become Chicks in hand.
- Dropping a Lion is impossible because Lion capture ends the game instead of
  entering hand.

## Promotion

A Chick promotes to Hen only when it reaches the opponent's home rank as the
result of a move.

- Black Chick promotes after moving to `rank == 3`.
- White Chick promotes after moving to `rank == 0`.
- Promotion is mandatory.
- Dropping a Chick on the promotion rank does not promote it.
- A Chick already on the promotion rank due to a drop has no legal forward move,
  so it cannot later promote unless some variant-specific rule is added. This
  repo should not add such a rule.

## Lion Try Rule

A player can win by moving their Lion onto the opponent's home rank if the Lion
cannot be captured by the opponent on the opponent's next move.

For engine implementation, resolve a Lion move to the opponent home rank in
this order:

1. Apply the Lion move and any capture on its destination.
2. If the opposing Lion was captured, the mover wins by capture.
3. Otherwise, test whether the opponent has any legal one-ply move that captures
   the moved Lion.
4. If no such capture exists, the mover wins by try.
5. If such a capture exists, the position remains non-terminal and the opponent
   moves next.

This matches lishogi's explicit "cannot be captured on the next move" wording
and the Nestor rulebook's note that a Lion may not be placed in the opponent's
last square if that would put it in check. Some physical rule sheets summarize
the rule as simply reaching the opponent's home; this repo uses the explicit
safe-try version to avoid awarding wins to capturable Lions.

## Terminal Conditions

The engine should expose terminal states with a reason:

- `LION_CAPTURE`: side to move captures the opponent Lion and wins.
- `SAFE_TRY`: side to move moves its Lion to the opponent's home rank and that
  Lion is not capturable on the opponent's next move.
- `REPETITION_DRAW`: the same full position occurs for the third time.

The "same full position" should include:

- Board piece kind, owner, and promotion state.
- Side to move.
- Hand contents for both players.

Do not implement checkmate as a separate terminal condition in the first engine
pass. Since capturing the Lion is the primary objective, check/checkmate can be
derived later for UI messages or tactics tests if needed.

## Draws, Repetition, And Step Caps

The Nestor rulebook states a game is drawn if a position repeats 3 times.
lishogi's public variant page does not mention repetition, while other online
summaries sometimes refer to Shogi-like fourfold repetition or perpetual check.

Repo default:

- Implement third occurrence of the same full position as a draw.
- Count the initial position as the first occurrence.
- Do not add a Shogi perpetual-check special loss rule in the first pass.
- Do not add an engine-level fifty-move rule or maximum step rule.
- Training/evaluation code may later impose an episode cap, but it must report
  that as `STEP_LIMIT_DRAW` or another wrapper-level result, not a core rules
  result.

## Ambiguities And Source Differences

- Try rule wording differs. Nestor's game-end bullet says reaching the
  opponent's home wins, but the movement section forbids placing the Lion on the
  opponent's last square if it would be in check. lishogi phrases this as a win
  only when the Lion cannot be captured next. Use safe-try.
- Repetition differs or is omitted. Nestor says third repetition is a draw.
  lishogi omits repetition on the public page. Some general Shogi material uses
  fourfold repetition. Use third occurrence for this repo and document it in
  tests.
- Chick drops on the last rank are easy to misread because Shogi normally has
  pawn-drop restrictions. lishogi explicitly says Dobutsu has no drop
  restrictions, including last-rank Chick drops. Nestor also says a re-entered
  Chick on the opponent's home does not grow up. Use unrestricted drops.
- No public source reviewed here defines stalemate/no-legal-move behavior. With
  unrestricted drops and Lion movement, this is unlikely but should still be
  guarded in implementation. If reached, prefer raising an invariant error in
  tests until a real legal position demonstrates it.
- Public rules do not specify a canonical notation. Choose a simple internal
  notation later after state/action dataclasses are defined.

## Engine Implementation Implications

- Keep `engine/` pure Python and rules-only.
- Make `GameState` immutable or treat it as persistent; legal move generation
  should return new states rather than mutating shared state.
- Store side-to-move, board, hands, terminal result, and repetition history in
  explicit fields.
- Represent Hen on the board, but never in hand.
- Normalize captured Hen to Chick at capture time.
- Keep attack detection separate from legal action generation so the safe-try
  test is simple and covered directly.
- Generate legal actions from the current state, then filter/score terminal
  transitions.
- Include source-backed unit tests for each rule: setup, piece movement,
  captures, demotion, drops, promotion-on-move only, safe try, unsafe try,
  repetition draw, and terminal capture.

## Action Encoding Recommendations

For the first rules engine, expose test-friendly structured actions:

- `MoveAction(from_square, to_square)`
- `DropAction(piece_kind, to_square)`

For future RL adapters, use a fixed action space plus an illegal-action mask.
A compact default is:

- Move actions: `12 source squares * 8 destination directions = 96`.
- Drop actions: `3 droppable piece kinds * 12 target squares = 36`.
- Total fixed action slots: `132`.

Droppable kinds are Chick, Giraffe, and Elephant. A rectangular `144`-slot
layout may reserve unused Lion/Hen drop slots later if an adapter strongly
prefers a uniform table, but the recommended first RL design is `132` because it
contains only piece kinds that can legally exist in hand.

The engine itself should not depend on this fixed encoding. It should return a
variable-length list of legal structured actions; training adapters can map
them to fixed indices.

## Observation Encoding Recommendations

Keep the canonical engine state human-readable. Add ML observation adapters
after the rules engine is stable.

Recommended first ML observation:

- Perspective-normalized planes from the side to move.
- Board planes for own/opponent pieces by kind:
  `2 owners * 5 board kinds = 10` planes over `4 x 3`.
- Hand count planes or scalar features for each side and hand piece kind:
  Chick, Giraffe, Elephant. Hen and Lion are excluded from hand.
- Side-to-move is implicit if perspective-normalized; include an explicit
  side-to-move scalar only for non-normalized debug encodings.
- Optional repetition count feature for each state key if repetition draw is
  active in training.

For tests and replay, prefer a readable serialization before optimizing for ML:

- Board array/list with `(owner, kind)` or `null`.
- Hands as per-side piece counts.
- Side to move.
- Terminal result if any.

## Sources

- Nekomado announcement linking official multilingual Dobutsu Shogi rule papers:
  https://nekomado.com/news/8997/
- Nekomado English rule paper:
  https://nekomado.com/wp/wp-content/uploads/2021/12/en.pdf
- Nekomado quick guide:
  https://nekomado.com/wp/wp-content/uploads/2021/12/QD_en.pdf
- Nestor Games / Let's Catch the Lion English rulebook:
  https://nestorgames.com/rulebooks/LION_EN.pdf
- lishogi Dobutsu variant page:
  https://lishogi.org/variant/dobutsu
