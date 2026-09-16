"""Headline typography.

Two things the original got loose and this tightens up:

* Vertical centring used ``(height - bbox[3]) // 2``, which throws away the
  bbox top. On a 1200px canvas that left the headline ~15px below true centre.
* Tracking was a flat -3px, which is correct at the 144pt it was written for
  and wrong at every other size. It is an em fraction here, so it holds.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..errors import RenderError

# Headline height as a fraction of the canvas, and the em-relative letter
# spacing. Both were reverse-engineered from the original 144pt/-3px pair at
# 1200px tall so existing covers keep their proportions.
FONT_SIZE_RATIO = 0.12
DEFAULT_TRACKING_EM = -0.021

# Never let a headline run closer than this to the canvas edge.
SAFE_WIDTH_RATIO = 0.86


def default_font_path() -> Path:
    """Path to the bundled Inter Bold, resolved through the package, not the cwd."""
    return Path(str(resources.files("notion_bg_gen.data").joinpath("Inter-Bold.ttf")))


def load_font(size: int, font_path: Path | None = None) -> ImageFont.FreeTypeFont:
    path = font_path or default_font_path()
    try:
        return ImageFont.truetype(str(path), size)
    except OSError as exc:
        raise RenderError(
            f"Could not load the font at {path}: {exc}",
            hint="Pass --font with a path to a .ttf or .otf file.",
        ) from None


def _advance(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> float:
    return float(font.getlength(text))


def measure(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking: float,
) -> float:
    """Total drawn width including the tracking applied between characters."""
    if not text:
        return 0.0
    return sum(_advance(draw, ch, font) for ch in text) + tracking * (len(text) - 1)


def draw_headline(
    image: Image.Image,
    text: str,
    color: tuple[int, int, int],
    *,
    font_path: Path | None = None,
    tracking_em: float = DEFAULT_TRACKING_EM,
) -> None:
    """Draw `text` centred on `image`, shrinking it to fit if it would overflow."""
    text = text.strip()
    if not text:
        return

    width, height = image.size
    draw = ImageDraw.Draw(image)

    size = max(8, int(height * FONT_SIZE_RATIO))
    font = load_font(size, font_path)
    tracking = tracking_em * size

    # Shrink to fit rather than letting a long title run off the canvas.
    limit = width * SAFE_WIDTH_RATIO
    total = measure(draw, text, font, tracking)
    if total > limit:
        size = max(8, int(size * limit / total))
        font = load_font(size, font_path)
        tracking = tracking_em * size
        total = measure(draw, text, font, tracking)

    # Centre on the ink box, including its top offset, so the optical centre of
    # the glyphs lands on the centre of the canvas.
    box = draw.textbbox((0, 0), text, font=font)
    text_y = (height - (box[3] - box[1])) // 2 - box[1]
    x = (width - total) / 2.0

    for char in text:
        draw.text((x, text_y), char, font=font, fill=color)
        x += _advance(draw, char, font) + tracking


# --- Contrast -------------------------------------------------------------
#
# A theme fixes the headline colour, but a palette can put anything behind it:
# the "forest" palette on the light theme paints a dark green field under text
# meant to be near-black. Rather than forbid those combinations, measure what
# actually ended up behind the headline and pick a colour that stays readable.

_LIGHT_INK = (250, 250, 250)
_DARK_INK = (9, 9, 11)

# WCAG AA for large text. Headlines here are ~14% of the canvas height, which is
# comfortably "large", so 3:1 is the bar to clear rather than 4.5:1.
MIN_CONTRAST_RATIO = 3.0


def _relative_luminance(rgb: tuple[float, float, float]) -> float:
    """WCAG relative luminance for an sRGB triple in 0..255."""
    channels = []
    for value in rgb:
        srgb = value / 255.0
        channels.append(srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    """WCAG contrast ratio between two colours, from 1.0 to 21.0."""
    lum_a, lum_b = _relative_luminance(a), _relative_luminance(b)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def pick_text_color(
    backdrop: tuple[float, float, float],
    preferred: tuple[int, int, int],
) -> tuple[int, int, int]:
    """Keep the theme's headline colour when it is legible, else swap the ink.

    `backdrop` is the mean colour behind the headline, not the theme background,
    so a pale gradient over a dark theme is handled the same as the reverse.
    """
    if contrast_ratio(backdrop, preferred) >= MIN_CONTRAST_RATIO:
        return preferred

    light_ratio = contrast_ratio(backdrop, _LIGHT_INK)
    dark_ratio = contrast_ratio(backdrop, _DARK_INK)
    return _LIGHT_INK if light_ratio >= dark_ratio else _DARK_INK
