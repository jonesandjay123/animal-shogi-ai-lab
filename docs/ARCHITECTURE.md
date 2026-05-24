# Architecture

## Design Principle

Keep the project layered. Game correctness is the foundation; learning code should depend on the engine, not redefine the game.

## Layers

```text
engine
  Pure rules, legal actions, game state, serialization.

agents
  Stateless or lightly stateful policies that choose actions from legal actions.

training
  Self-play, environment adapters, replay collection, model training.

eval
  Match runners, rating, regression checks, benchmark reports.

web
  Optional browser UI/demo using serialized game states and actions.
```

## Engine Contract

The engine should expose a small API:

- `GameState`: immutable or copy-safe game position.
- `Action`: move or drop.
- `legal_actions(state) -> list[Action]`.
- `apply_action(state, action) -> GameState`.
- `is_terminal(state) -> bool`.
- `winner(state) -> Player | None`.
- `serialize(state) -> str | dict`.
- `deserialize(payload) -> GameState`.

## Agent Contract

Agents should never mutate state directly. They receive a state and legal actions, then return one action.

```python
class Agent(Protocol):
    def select_action(self, state: GameState, legal_actions: Sequence[Action]) -> Action:
        ...
```

## Training Contract

Training code should consume the public engine API only. If training needs faster representations later, add adapters in `training/` rather than leaking ML-specific arrays into `engine/`.

## Reproducibility

Every experiment should record:

- Git commit.
- Config file.
- Random seed.
- Agent/model versions.
- Number of games.
- Evaluation opponent and score.
