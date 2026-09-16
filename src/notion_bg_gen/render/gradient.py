"""Gradient field generation.

Every style takes an RNG and a list of accent colours and returns a premultiplied
colour field plus its coverage mask. The engine composites that over the theme
background, so styles never need to know what they are being drawn onto.

The original implementation drew ~600 concentric PIL ellipses and then asked for
a 300px Gaussian blur at 3000x1200, which dominated the runtime. The same shapes
are built here as numpy distance fields, and large blurs run on a downsampled
copy - a 300px blur carries no detail that survives an 8x round trip.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import numpy.typing as npt

from ..errors import UsageError

FloatArray = npt.NDArray[np.float32]
Field = tuple[FloatArray, FloatArray]  # (rgb HxWx3 in 0..255, alpha HxW in 0..1)


def _box_blur_1d(array: FloatArray, radius: int, axis: int) -> FloatArray:
    """One box-blur pass along an axis, via a summed-area table.

    Cost is independent of the radius, which matters here: the mesh style asks
    for a 300px blur, where a direct convolution would touch 601 taps per pixel.
    """
    if radius < 1:
        return array

    moved = np.moveaxis(array, axis, 0)
    length = moved.shape[0]
    pad = [(radius + 1, radius)] + [(0, 0)] * (moved.ndim - 1)
    padded = np.pad(moved, pad, mode="edge")

    # float64 keeps the running sum honest across a few thousand samples.
    cumulative = np.cumsum(padded, axis=0, dtype=np.float64)
    window = 2 * radius + 1
    out = (cumulative[window : window + length] - cumulative[0:length]) / window
    return np.moveaxis(out.astype(np.float32), 0, axis)


def blur(array: FloatArray, sigma: float) -> FloatArray:
    """Approximate a Gaussian blur with three successive box passes.

    Three boxes land within a couple of percent of a true Gaussian, which is far
    inside what survives being composited under a grain pass.
    """
    if sigma <= 0:
        return array

    passes = 3
    # Width whose variance after `passes` convolutions matches the target sigma.
    width = np.sqrt(12.0 * sigma * sigma / passes + 1.0)
    radius = max(1, round((width - 1) / 2))

    out = array.astype(np.float32, copy=True)
    for _ in range(passes):
        out = _box_blur_1d(out, radius, axis=0)
        out = _box_blur_1d(out, radius, axis=1)
    return out


def _grid(width: int, height: int) -> tuple[FloatArray, FloatArray]:
    ys, xs = np.mgrid[0:height, 0:width]
    return xs.astype(np.float32), ys.astype(np.float32)


def _over(base: Field, src_rgb: FloatArray, src_alpha: FloatArray) -> Field:
    """Composite a source layer over an accumulating field ("source over")."""
    base_rgb, base_alpha = base
    a = src_alpha[..., None]
    rgb = src_rgb * a + base_rgb * (1.0 - a)
    alpha = src_alpha + base_alpha * (1.0 - src_alpha)
    return rgb, alpha


def _bottom_ellipse_mask(width: int, height: int) -> FloatArray:
    """The wide, low ellipse that keeps the glow anchored to the bottom edge.

    Carried over from the original renderer - it is what stops the gradient
    reading as a full-bleed wash and gives the covers their horizon line.
    """
    xs, ys = _grid(width, height)
    rx = width * 1.5 / 2.0
    ry = height * 1.2 / 2.0
    cx = width / 2.0
    cy = float(height)
    d = ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2
    return (d <= 1.0).astype(np.float32)


def style_mesh(
    width: int, height: int, colors: list[tuple[int, int, int]], rng: np.random.Generator
) -> Field:
    """Overlapping radial blobs, masked to the lower ellipse and heavily blurred."""
    field: Field = (np.zeros((height, width, 3), np.float32), np.zeros((height, width), np.float32))
    xs, ys = _grid(width, height)
    scale = min(width, height) / 1200.0

    for _ in range(10):
        cx = rng.uniform(0, width)
        cy = rng.uniform(0, height)
        radius = rng.uniform(0.5, 1.0) * (width + height) / 2.0
        colour = np.array(colors[rng.integers(len(colors))], np.float32)

        dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        # The original drew shrinking rings whose alpha fell with the radius,
        # leaving the centre sheer and the rim solid. Reproduced directly.
        alpha = np.clip(dist / radius, 0.0, 1.0).astype(np.float32)
        alpha[dist > radius] = 0.0
        field = _over(field, np.broadcast_to(colour, (height, width, 3)).copy(), alpha)

    rgb, alpha = field
    alpha = alpha * _bottom_ellipse_mask(width, height)
    sigma = 300.0 * scale
    return blur(rgb, sigma), blur(alpha, sigma)


def style_aurora(
    width: int, height: int, colors: list[tuple[int, int, int]], rng: np.random.Generator
) -> Field:
    """Soft horizontal curtains with a sine warp, brightest low on the canvas."""
    xs, ys = _grid(width, height)
    scale = min(width, height) / 1200.0
    field: Field = (np.zeros((height, width, 3), np.float32), np.zeros((height, width), np.float32))

    bands = min(len(colors), 6)
    for _i in range(bands):
        colour = np.array(colors[rng.integers(len(colors))], np.float32)
        centre = height * rng.uniform(0.35, 1.05)
        thickness = height * rng.uniform(0.25, 0.6)
        warp = np.sin(xs / width * np.pi * rng.uniform(1.0, 3.0) + rng.uniform(0, 6.28)) * (
            height * rng.uniform(0.05, 0.18)
        )
        dist = np.abs(ys - (centre + warp))
        alpha = np.clip(1.0 - dist / thickness, 0.0, 1.0).astype(np.float32) ** 1.5
        field = _over(field, np.broadcast_to(colour, (height, width, 3)).copy(), alpha * 0.85)

    rgb, alpha = field
    sigma = 120.0 * scale
    return blur(rgb, sigma), blur(alpha, sigma)


def style_blobs(
    width: int, height: int, colors: list[tuple[int, int, int]], rng: np.random.Generator
) -> Field:
    """Fewer, tighter, higher-contrast orbs - closer to a metaball render."""
    xs, ys = _grid(width, height)
    scale = min(width, height) / 1200.0
    field: Field = (np.zeros((height, width, 3), np.float32), np.zeros((height, width), np.float32))

    # Radius keys off the canvas height, not its smaller dimension: a 3840x1200
    # banner needs the same visual blob size as a 1500x600 cover, and scaling by
    # min(w, h) shrinks them into a smudge as the canvas gets wider.
    for i in range(8):
        # Stratify horizontally so the blobs span the canvas instead of clumping.
        band = (i + rng.uniform(0.15, 0.85)) / 8.0
        cx = band * width
        cy = rng.uniform(height * 0.1, height * 1.1)
        radius = rng.uniform(0.55, 1.2) * height
        colour = np.array(colors[rng.integers(len(colors))], np.float32)
        dist = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
        alpha = np.clip(1.0 - (dist / radius) ** 2, 0.0, 1.0).astype(np.float32)
        field = _over(field, np.broadcast_to(colour, (height, width, 3)).copy(), alpha)

    rgb, alpha = field
    sigma = 90.0 * scale
    return blur(rgb, sigma), blur(alpha, sigma)


def style_linear(
    width: int, height: int, colors: list[tuple[int, int, int]], rng: np.random.Generator
) -> Field:
    """A clean multi-stop linear sweep at a shallow angle. The restrained option."""
    xs, ys = _grid(width, height)
    angle = rng.uniform(-0.35, 0.35)
    t = xs * np.cos(angle) + ys * np.sin(angle)
    t = (t - t.min()) / max(float(t.max() - t.min()), 1e-6)

    stops = [colors[int(rng.integers(len(colors)))] for _ in range(min(len(colors), 4))]
    positions = np.linspace(0.0, 1.0, len(stops), dtype=np.float32)
    rgb = np.zeros((height, width, 3), np.float32)
    for channel in range(3):
        values = np.array([s[channel] for s in stops], np.float32)
        rgb[:, :, channel] = np.interp(t, positions, values).astype(np.float32)

    # Fade the top edge so a headline still has somewhere quiet to sit.
    alpha = np.clip(ys / height * 1.4, 0.0, 1.0).astype(np.float32)
    return rgb, alpha


StyleFn = Callable[[int, int, list[tuple[int, int, int]], np.random.Generator], Field]

STYLES: dict[str, StyleFn] = {
    "mesh": style_mesh,
    "aurora": style_aurora,
    "blobs": style_blobs,
    "linear": style_linear,
}

STYLE_DESCRIPTIONS: dict[str, str] = {
    "mesh": "Overlapping radial blobs under a heavy blur. The original look.",
    "aurora": "Soft horizontal curtains with a sine warp.",
    "blobs": "Fewer, tighter, higher-contrast orbs.",
    "linear": "A clean multi-stop linear sweep. The restrained option.",
}

DEFAULT_STYLE = "mesh"


def resolve_style(name: str) -> StyleFn:
    if name not in STYLES:
        known = ", ".join(STYLES)
        raise UsageError(f"Unknown style {name!r}.", hint=f"Available styles: {known}")
    return STYLES[name]
