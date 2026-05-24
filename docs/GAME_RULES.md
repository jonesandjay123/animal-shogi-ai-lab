# Animal Shogi Rules Notes

This file is a working spec for the implementation. Verify details before coding edge cases.

## Board

- 3 columns x 4 rows.
- Two players face opposite directions.
- Coordinates should be explicit and documented before engine implementation.

## Pieces

- Lion
- Giraffe
- Elephant
- Chick
- Hen, promoted chick

## Movement

Use player-relative movement where needed.

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

The engine should encode one explicit ruleset and document any variants.
