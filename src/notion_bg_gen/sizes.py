"""Named output dimensions.

Notion renders a page cover into a band roughly 2.5:1, and its own guidance
asks for at least 1500x600. ``cover@2x`` is that band at twice the resolution,
which is what looks right on a HiDPI display, so it is the default.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from .errors import UsageError


class Size(NamedTuple):
    width: int
    height: int

    def __str__(self) -> str:
        return f"{self.width}x{self.height}"


NAMED_SIZES: dict[str, Size] = {
    "cover": Size(1500, 600),
    "cover@2x": Size(3000, 1200),
    "wide": Size(3840, 1200),
    "square": Size(1200, 1200),
}

DEFAULT_SIZE = "cover@2x"

_CUSTOM = re.compile(r"^(\d{2,5})\s*[x×]\s*(\d{2,5})$", re.IGNORECASE)

# Guard rails: a 20000x20000 request would allocate ~4.8GB of float32 per
# channel buffer and look like a hang rather than a mistake.
MAX_DIMENSION = 10000
MIN_DIMENSION = 64


def parse_size(value: str) -> Size:
    """Resolve a named size or a literal ``WIDTHxHEIGHT`` string."""
    key = value.strip().lower()
    if key in NAMED_SIZES:
        return NAMED_SIZES[key]

    match = _CUSTOM.match(key)
    if not match:
        names = ", ".join(NAMED_SIZES)
        raise UsageError(
            f"Unknown size {value!r}.",
            hint=f"Use one of: {names} - or a literal size such as 2000x800.",
        )

    width, height = int(match.group(1)), int(match.group(2))
    for dim, label in ((width, "width"), (height, "height")):
        if dim < MIN_DIMENSION:
            raise UsageError(f"The {label} {dim} is below the {MIN_DIMENSION}px minimum.")
        if dim > MAX_DIMENSION:
            raise UsageError(f"The {label} {dim} is above the {MAX_DIMENSION}px maximum.")
    return Size(width, height)
