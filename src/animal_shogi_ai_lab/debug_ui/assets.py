"""Asset loading for the Pygame debug board."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from animal_shogi_ai_lab.engine import PieceKind, Player

SPRITE_SHEET_RELATIVE_PATH = Path("assets/pieces/animal_pieces_sprite_sheet.png")
SPRITE_SHEET_COLUMNS = 5

PIECE_SPRITE_INDEX = {
    PieceKind.CHICK: 0,
    PieceKind.HEN: 1,
    PieceKind.LION: 2,
    PieceKind.GIRAFFE: 3,
    PieceKind.ELEPHANT: 4,
}


def default_sprite_sheet_path() -> Path:
    cwd_candidate = Path.cwd() / SPRITE_SHEET_RELATIVE_PATH
    if cwd_candidate.exists():
        return cwd_candidate.resolve()
    return Path(__file__).resolve().parents[3] / SPRITE_SHEET_RELATIVE_PATH


def load_piece_sprites(pygame: Any, path: Path | None = None) -> dict[PieceKind, Any]:
    sprite_path = path or default_sprite_sheet_path()
    if not sprite_path.exists():
        return {}

    try:
        sheet = pygame.image.load(str(sprite_path)).convert_alpha()
    except Exception:
        return {}

    sheet_width, sheet_height = sheet.get_size()
    sprite_width = sheet_width // SPRITE_SHEET_COLUMNS
    if sprite_width <= 0 or sheet_height <= 0:
        return {}

    sprites = {}
    for kind, index in PIECE_SPRITE_INDEX.items():
        rect = pygame.Rect(index * sprite_width, 0, sprite_width, sheet_height)
        sprites[kind] = sheet.subsurface(rect).copy()
    return sprites


def oriented_sprite(pygame: Any, sprite: Any, owner: Player) -> Any:
    if owner is Player.WHITE:
        return pygame.transform.rotate(sprite, 180)
    return sprite


def scale_to_fit(pygame: Any, sprite: Any, max_width: int, max_height: int) -> Any:
    width, height = sprite.get_size()
    if width <= 0 or height <= 0:
        return sprite
    scale = min(max_width / width, max_height / height)
    target_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return pygame.transform.smoothscale(sprite, target_size)


__all__ = [
    "PIECE_SPRITE_INDEX",
    "SPRITE_SHEET_COLUMNS",
    "SPRITE_SHEET_RELATIVE_PATH",
    "default_sprite_sheet_path",
    "load_piece_sprites",
    "oriented_sprite",
    "scale_to_fit",
]
