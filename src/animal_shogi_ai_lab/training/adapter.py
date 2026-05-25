from __future__ import annotations

import numpy as np

from animal_shogi_ai_lab.engine import (
    Action,
    DropAction,
    GameState,
    MoveAction,
    PieceKind,
    Player,
    Square,
)

# Move direction offsets (from Black's perspective / absolute board coordinates)
# 0: NW, 1: N, 2: NE, 3: W, 4: E, 5: SW, 6: S, 7: SE
DIRECTIONS = [
    (-1, 1),   # 0: NW
    (0, 1),    # 1: N
    (1, 1),    # 2: NE
    (-1, 0),   # 3: W
    (1, 0),    # 4: E
    (-1, -1),  # 5: SW
    (0, -1),   # 6: S
    (1, -1),   # 7: SE
]

PIECE_KIND_TO_INDEX = {
    PieceKind.LION: 0,
    PieceKind.GIRAFFE: 1,
    PieceKind.ELEPHANT: 2,
    PieceKind.CHICK: 3,
    PieceKind.HEN: 4,
}

INDEX_TO_PIECE_KIND = {v: k for k, v in PIECE_KIND_TO_INDEX.items()}

DROP_KINDS = [PieceKind.CHICK, PieceKind.GIRAFFE, PieceKind.ELEPHANT]


def encode_action(action: Action) -> int:
    """Maps a structured MoveAction or DropAction to a unique integer in [0, 131]."""
    if isinstance(action, MoveAction):
        df = action.to_square.file - action.from_square.file
        dr = action.to_square.rank - action.from_square.rank
        direction = (df, dr)
        if direction not in DIRECTIONS:
            raise ValueError(f"Invalid move direction delta: {direction}")
        direction_idx = DIRECTIONS.index(direction)
        source_idx = action.from_square.rank * 3 + action.from_square.file
        return source_idx * 8 + direction_idx

    elif isinstance(action, DropAction):
        if action.piece_kind not in DROP_KINDS:
            raise ValueError(f"Invalid piece kind for dropping: {action.piece_kind}")
        kind_idx = DROP_KINDS.index(action.piece_kind)
        dest_idx = action.to_square.rank * 3 + action.to_square.file
        return 96 + kind_idx * 12 + dest_idx

    raise TypeError(f"Unknown action type: {type(action)}")


def decode_action(index: int) -> Action:
    """Decodes a unique action index in [0, 131] to a structured MoveAction or DropAction."""
    if not (0 <= index < 132):
        raise ValueError(f"Action index {index} out of range [0, 131].")

    if index < 96:
        source_idx = index // 8
        direction_idx = index % 8
        from_file = source_idx % 3
        from_rank = source_idx // 3
        df, dr = DIRECTIONS[direction_idx]
        to_file = from_file + df
        to_rank = from_rank + dr
        return MoveAction(Square(from_file, from_rank), Square(to_file, to_rank))
    else:
        drop_offset = index - 96
        kind_idx = drop_offset // 12
        dest_idx = drop_offset % 12
        to_file = dest_idx % 3
        to_rank = dest_idx // 3
        piece_kind = DROP_KINDS[kind_idx]
        return DropAction(piece_kind, Square(to_file, to_rank))


def legal_action_mask(state: GameState) -> np.ndarray:
    """Returns a boolean array of shape (132,) where True indicates a legal action."""
    mask = np.zeros(132, dtype=np.bool_)
    if state.is_terminal():
        return mask

    for action in state.legal_actions():
        try:
            idx = encode_action(action)
            mask[idx] = True
        except ValueError:
            # Just in case an action is illegal or doesn't map correctly
            pass
    return mask


def encode_observation(state: GameState) -> np.ndarray:
    """Encodes a GameState into a perspective-normalized float32 array of shape (126,)."""
    # 10 planes of 4x3: 0..4 are own pieces, 5..9 are opponent pieces.
    # Order: LION, GIRAFFE, ELEPHANT, CHICK, HEN.
    obs_planes = np.zeros((10, 4, 3), dtype=np.float32)

    side = state.side_to_move
    opponent = side.opponent

    for square, piece in state.board.items():
        is_own = (piece.owner is side)
        kind_idx = PIECE_KIND_TO_INDEX[piece.kind]
        plane_idx = kind_idx if is_own else 5 + kind_idx

        # Perspective rotation:
        # If side is Black, no change.
        # If side is White, rotate 180 degrees.
        if side is Player.BLACK:
            f = square.file
            r = square.rank
        else:
            f = 2 - square.file
            r = 3 - square.rank

        obs_planes[plane_idx, r, f] = 1.0

    # Hand counts: 6 elements
    # own_chick, own_giraffe, own_elephant, opp_chick, opp_giraffe, opp_elephant
    hands = state.hands
    hand_features = [
        float(hands[side].get(PieceKind.CHICK, 0)),
        float(hands[side].get(PieceKind.GIRAFFE, 0)),
        float(hands[side].get(PieceKind.ELEPHANT, 0)),
        float(hands[opponent].get(PieceKind.CHICK, 0)),
        float(hands[opponent].get(PieceKind.GIRAFFE, 0)),
        float(hands[opponent].get(PieceKind.ELEPHANT, 0)),
    ]

    flat_obs = np.concatenate([obs_planes.flatten(), np.array(hand_features, dtype=np.float32)])
    return flat_obs
