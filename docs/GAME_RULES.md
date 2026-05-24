# Animal Shogi Rules Spec

Status: Draft / Pending external rule research

This file is a working rules spec for implementation. It is not final yet. The next agent pass should research Dōbutsu Shōgi / Animal Shogi rules from public sources, update this file, and stop before implementing game logic.

## Confirmed Scaffold Assumptions

- The target game is Animal Shogi / Dōbutsu Shōgi.
- The engine should encode one explicit ruleset, not a loose mixture of variants.
- Coordinates, action encoding, and terminal state semantics must be documented before engine implementation.

## Board

- 3 columns x 4 rows.
- Two players face opposite directions.
- Coordinates should be explicit and documented before engine implementation.
- Initial setup must be verified and documented before coding.

## Pieces

- Lion
- Giraffe
- Elephant
- Chick
- Hen, promoted chick

## Movement

Use player-relative movement where needed. Exact relative deltas must be verified before implementation.

- Lion: one square in any direction.
- Giraffe: one square orthogonally.
- Elephant: one square diagonally.
- Chick: one square forward.
- Hen: gold-general-like movement for Animal Shogi; verify exact relative deltas before implementation.

## Captures And Drops

- Captured pieces go into the capturing player's hand.
- Promoted chicks should demote when captured.
- Players may drop pieces from hand onto empty squares.
- Verify whether any drop restrictions apply in the intended rule set.

## Promotion

- Chick promotes to hen when reaching the far rank.
- Promotion and demotion rules should be covered with tests.

## Win Conditions

Common win conditions to verify:

- Capture the opponent lion.
- Try rule: a lion reaching the far rank can win if it is not immediately capturable.

## Needs Confirmation

- Exact coordinate convention and orientation.
- Exact initial setup.
- Exact hen movement.
- Whether any chick drop restrictions exist.
- Exact lion try rule timing.
- Whether check/checkmate exists as a required concept or only terminal capture/try states matter.
- Repetition / draw handling.
- Maximum move limit for AI self-play and evaluation.
- Whether stalemate-like no-legal-action states are possible and how to score them.
- Canonical notation or replay format, if any.

## Implementation Implications To Decide

- Whether `GameState` should be immutable.
- Whether actions should use a fixed action space, a legal-action list, or both.
- How to represent pieces in hand.
- How to represent promoted pieces during capture/demotion.
- How to serialize states for replay, tests, and future UI.
- How to expose action masks for RL.

## Rule Variants

Document any discovered rule variants here before coding. The engine should choose one default ruleset and name it explicitly.
