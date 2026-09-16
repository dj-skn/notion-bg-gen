"""Film grain.

The original renderer built noise with ``np.random.normal(0, 25, ...)`` and then
called ``.astype(np.uint8)``. Roughly half of a zero-centred normal is negative,
and those samples wrap rather than clamp, so about 47% of the "grain" landed at
200-255 and the result was salt-and-pepper rather than a soft tooth. Here the
noise is added as a signed delta in float space and clipped once, at the end.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float32]

# Grain strength 1.0 maps to this standard deviation on a 0-255 scale.
_MAX_SIGMA = 20.0

DEFAULT_GRAIN = 0.35


def apply_grain(image: FloatArray, amount: float, rng: np.random.Generator) -> FloatArray:
    """Add luminance grain to a float image in 0..255 and clip to range.

    The noise is monochrome - one sample shared across R, G and B - because
    independent per-channel noise reads as colour speckle, while real film grain
    varies in density rather than hue.
    """
    if amount <= 0:
        return image

    sigma = _MAX_SIGMA * float(amount)
    noise = rng.normal(0.0, sigma, image.shape[:2]).astype(np.float32)
    grained: FloatArray = np.clip(image + noise[..., None], 0.0, 255.0)
    return grained
