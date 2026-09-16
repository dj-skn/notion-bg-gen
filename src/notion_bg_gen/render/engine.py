"""Turning a request into an image on disk."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import numpy.typing as npt
from PIL import Image

from ..errors import RenderError, UsageError
from ..sizes import Size
from .gradient import resolve_style
from .grain import DEFAULT_GRAIN, apply_grain
from .palette import Palette, Theme
from .text import DEFAULT_TRACKING_EM, draw_headline, pick_text_color

FORMATS: dict[str, str] = {"jpg": "JPEG", "png": "PNG", "webp": "WEBP"}
DEFAULT_FORMAT = "jpg"
DEFAULT_QUALITY = 92

# A seed has to survive a round trip through JSON and a --seed flag, so keep it
# inside the range a 64-bit signed integer can hold.
MAX_SEED = 2**63 - 1


@dataclass(frozen=True)
class CoverSpec:
    """Everything needed to produce one cover, with no I/O implied."""

    text: str | None
    palette: Palette
    theme: Theme
    size: Size
    style: str = "mesh"
    seed: int = field(default_factory=lambda: secrets.randbelow(MAX_SEED))
    grain: float = DEFAULT_GRAIN
    tracking: float = DEFAULT_TRACKING_EM
    font: Path | None = None
    text_color: tuple[int, int, int] | None = None
    image_format: str = DEFAULT_FORMAT
    quality: int = DEFAULT_QUALITY

    def __post_init__(self) -> None:
        if self.image_format not in FORMATS:
            raise UsageError(
                f"Unknown format {self.image_format!r}.",
                hint=f"Available formats: {', '.join(FORMATS)}",
            )
        if not 0 <= self.grain <= 1:
            raise UsageError(f"Grain must be between 0 and 1, got {self.grain}.")
        if not 1 <= self.quality <= 100:
            raise UsageError(f"Quality must be between 1 and 100, got {self.quality}.")


def _auto_text_color(
    canvas: npt.NDArray[np.float32], preferred: tuple[int, int, int]
) -> tuple[int, int, int]:
    """Choose ink based on what the gradient actually put behind the headline."""
    height, width = canvas.shape[:2]
    # The headline occupies the middle band; sample only that, since the corners
    # of a mesh gradient are often nothing like its centre.
    top, bottom = int(height * 0.35), int(height * 0.65)
    left, right = int(width * 0.07), int(width * 0.93)
    band = canvas[top:bottom, left:right]
    mean = tuple(float(v) for v in band.reshape(-1, 3).mean(axis=0))
    return pick_text_color((mean[0], mean[1], mean[2]), preferred)


def render(spec: CoverSpec) -> Image.Image:
    """Render a cover to an in-memory image.

    Deterministic for a given spec: the same seed reproduces the same bytes.
    """
    width, height = spec.size
    rng = np.random.default_rng(spec.seed)

    style_fn = resolve_style(spec.style)
    colors = spec.palette.rgb_for_theme(spec.theme.id)
    gradient_rgb, gradient_alpha = style_fn(width, height, colors, rng)

    # Composite the gradient over the flat theme background.
    background = np.array(spec.theme.background_rgb, np.float32)
    canvas = np.broadcast_to(background, (height, width, 3)).astype(np.float32)
    alpha = gradient_alpha[..., None]
    canvas = gradient_rgb * alpha + canvas * (1.0 - alpha)

    # Text goes on before grain, so the grain sits over the whole frame and the
    # headline picks up the same tooth as the background.
    image = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8), mode="RGB")
    if spec.text:
        draw_headline(
            image,
            spec.text,
            spec.text_color or _auto_text_color(canvas, spec.theme.text_rgb),
            font_path=spec.font,
            tracking_em=spec.tracking,
        )

    if spec.grain > 0:
        grained = apply_grain(np.asarray(image, dtype=np.float32), spec.grain, rng)
        image = Image.fromarray(grained.astype(np.uint8), mode="RGB")

    return image


def save(image: Image.Image, path: Path, *, image_format: str, quality: int) -> int:
    """Write the image and return its size in bytes."""
    pillow_format = FORMATS[image_format]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if pillow_format == "PNG":
            image.save(path, format=pillow_format, optimize=True)
        else:
            image.save(path, format=pillow_format, quality=quality, optimize=True)
    except OSError as exc:
        raise RenderError(
            f"Could not write {path}: {exc}",
            hint="Check that the directory is writable and the disk is not full.",
        ) from None
    return path.stat().st_size
