# Action And Observation Design

Status: Placeholder / Pending rule research

This file records how game states and legal moves will be encoded for agents and RL environments.

Do not implement neural training until this design is reviewed.

## Questions To Resolve

- Should the engine expose a variable-length legal-action list, a fixed action space, or both?
- How should illegal moves be masked for RL policies?
- How should the 3x4 board be encoded: piece IDs, planes/channels, or flat vectors?
- How should captured hand pieces be encoded?
- How should current player / side-to-move be encoded?
- How should promoted chicks / hens be represented?
- How should terminal states and rewards be represented?
- What state/action format should replays and the future web UI consume?

## Initial Direction

Keep the pure engine representation human-readable and test-friendly. Add ML-friendly adapters in `training/` after the rules are stable.

The engine should not depend on Torch, Gymnasium, or any neural-network-specific representation.
