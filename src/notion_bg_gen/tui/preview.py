"""Rendering a cover inside the terminal.

Each character cell shows two pixels: the upper half block takes the foreground
colour and the cell background takes the pixel below it. That doubles vertical
resolution for free, which matters when the whole preview is only a dozen rows.
"""

from __future__ import annotations

import numpy as np
from PIL import Image
from rich.color import Color
from rich.console import Console, ConsoleOptions, RenderResult
from rich.measure import Measurement
from rich.segment import Segment
from rich.style import Style

UPPER_HALF_BLOCK = "▀"


class HalfBlockImage:
    """A Rich renderable that draws a PIL image with half-block characters."""

    def __init__(self, image: Image.Image) -> None:
        self.image = image.convert("RGB")

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        # A numpy view beats PIL's pixel access here: it is faster per cell and
        # it types cleanly as an (H, W, 3) array rather than a mode-dependent union.
        pixels = np.asarray(self.image, dtype=np.uint8)
        height, width = pixels.shape[:2]

        for y in range(0, height - 1, 2):
            top_row = pixels[y]
            bottom_row = pixels[y + 1]
            for x in range(width):
                top = top_row[x]
                bottom = bottom_row[x]
                yield Segment(
                    UPPER_HALF_BLOCK,
                    Style(
                        color=Color.from_rgb(float(top[0]), float(top[1]), float(top[2])),
                        bgcolor=Color.from_rgb(
                            float(bottom[0]), float(bottom[1]), float(bottom[2])
                        ),
                    ),
                )
            yield Segment.line()

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        """One cell per pixel column, so the widget sizes to the image exactly."""
        width = self.image.size[0]
        return Measurement(width, width)


def fit_preview_pixels(cell_width: int, aspect: float, max_rows: int) -> tuple[int, int]:
    """Pixel dimensions that fill `cell_width` cells without exceeding `max_rows`.

    `aspect` is width / height of the target cover. Two pixels stack per row, so
    a cover that is 2.5:1 occupies cell_width / 5 rows.
    """
    cell_width = max(8, cell_width)
    px_width = cell_width
    px_height = max(2, round(px_width / aspect))

    rows = px_height / 2
    if rows > max_rows:
        px_height = max(2, max_rows * 2)
        px_width = max(8, round(px_height * aspect))

    # Half blocks need an even pixel height to pair up cleanly.
    if px_height % 2:
        px_height += 1
    return px_width, px_height
