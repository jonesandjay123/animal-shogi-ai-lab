# Legacy Audit Prompt

Use this prompt only after `docs/GAME_RULES.md` has been researched and reviewed.

```text
After docs/GAME_RULES.md is reviewed, inspect the legacy Animal Shogi repositories.

Compare the old implementation against the written rules spec.

Identify:

1. Reusable logic.
2. Incorrect or risky logic.
3. UI assets that can be reused.
4. RL environment design problems.
5. Action-space and observation-space issues.
6. Code that should be discarded.
7. Migration plan into this repo.

Do not copy legacy code blindly.
Do not merge old architecture into this repo without explaining why it matches the new spec.
Do not implement the migration in this phase unless explicitly asked.
```

Expected output: an audit report and migration plan, not a code port.
