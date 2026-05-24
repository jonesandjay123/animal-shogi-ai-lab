# Rule Research Prompt

Use this prompt for the first Codex implementation/research phase.

```text
Research Dōbutsu Shōgi / Animal Shogi rules from public sources first.

Do not inspect or rely on legacy code yet.
Do not implement the engine yet.

Create or update docs/GAME_RULES.md with:

1. Board coordinates.
2. Initial setup.
3. Piece movement.
4. Capture and hand rules.
5. Drop rules.
6. Chick promotion and demotion.
7. Lion try rule.
8. Terminal conditions.
9. Ambiguous rule variants.
10. Implementation implications.
11. Proposed action encoding.
12. Proposed observation encoding.
13. Sources used.

Stop after writing the rules spec.
Do not implement game logic in this phase.
```

Expected output: a reviewed, source-backed rules spec that is clear enough for a later clean engine implementation.
