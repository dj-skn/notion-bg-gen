"""Renderer behaviour, including the two defects that changed pixels."""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from notion_bg_gen.errors import UsageError
from notion_bg_gen.render.engine import CoverSpec, render, save
from notion_bg_gen.render.gradient import STYLES, blur
from notion_bg_gen.render.grain import apply_grain
from notion_bg_gen.render.text import (
    FONT_SIZE_RATIO,
    contrast_ratio,
    default_font_path,
    draw_headline,
    pick_text_color,
)
from notion_bg_gen.sizes import Size

SMALL = Size(300, 120)


def spec(classic, dark, **overrides):
    base = {"text": "Test", "palette": classic, "theme": dark, "size": SMALL, "seed": 42}
    base.update(overrides)
    return CoverSpec(**base)


# -- grain -----------------------------------------------------------------


def test_grain_does_not_blow_out_to_white():
    """Regression: noise was cast to uint8, wrapping ~half the samples to 200-255."""
    flat = np.full((64, 64, 3), 128.0, dtype=np.float32)
    out = apply_grain(flat, 0.35, np.random.default_rng(0))

    assert (out >= 200).mean() < 0.001
    assert (out <= 40).mean() < 0.001


def test_grain_preserves_the_mean():
    flat = np.full((128, 128, 3), 128.0, dtype=np.float32)
    out = apply_grain(flat, 0.5, np.random.default_rng(0))
    assert out.mean() == pytest.approx(128.0, abs=1.0)


def test_grain_stays_in_range_against_a_white_field():
    white = np.full((64, 64, 3), 255.0, dtype=np.float32)
    out = apply_grain(white, 1.0, np.random.default_rng(0))
    assert out.max() <= 255.0
    assert out.min() >= 0.0


def test_grain_is_monochrome():
    """Channels move together, which reads as film rather than colour speckle."""
    flat = np.full((32, 32, 3), 128.0, dtype=np.float32)
    out = apply_grain(flat, 0.5, np.random.default_rng(0))
    assert np.allclose(out[:, :, 0], out[:, :, 1])
    assert np.allclose(out[:, :, 1], out[:, :, 2])


def test_zero_grain_is_a_no_op():
    flat = np.full((16, 16, 3), 128.0, dtype=np.float32)
    assert np.array_equal(apply_grain(flat, 0.0, np.random.default_rng(0)), flat)


# -- blur ------------------------------------------------------------------


def test_blur_preserves_the_mean():
    field = np.random.default_rng(0).random((64, 64, 3)).astype(np.float32) * 255
    assert blur(field, 8.0).mean() == pytest.approx(field.mean(), abs=1.0)


def test_blur_flattens_an_impulse():
    field = np.zeros((64, 64, 1), dtype=np.float32)
    field[32, 32, 0] = 255.0
    assert blur(field, 6.0).max() < 255.0


def test_zero_sigma_is_a_no_op():
    field = np.ones((8, 8, 3), dtype=np.float32)
    assert np.array_equal(blur(field, 0.0), field)


# -- text ------------------------------------------------------------------


def test_bundled_font_resolves_without_a_cwd_assumption(tmp_path, monkeypatch):
    """Regression: assets used to load from the relative path "assets"."""
    monkeypatch.chdir(tmp_path)
    assert default_font_path().is_file()


def test_headline_is_vertically_centred():
    """Regression: centring dropped the bbox top and sat the text ~15px low."""
    height = 400
    image = Image.new("RGB", (1000, height), (0, 0, 0))
    draw_headline(image, "Hxy", (255, 255, 255))

    rows = np.asarray(image.convert("L")).max(axis=1)
    inked = np.flatnonzero(rows > 20)
    ink_centre = (inked[0] + inked[-1]) / 2

    assert ink_centre == pytest.approx(height / 2, abs=height * 0.02)


def test_headline_is_horizontally_centred():
    image = Image.new("RGB", (1000, 400), (0, 0, 0))
    draw_headline(image, "Hxy", (255, 255, 255))

    cols = np.asarray(image.convert("L")).max(axis=0)
    inked = np.flatnonzero(cols > 20)
    assert (inked[0] + inked[-1]) / 2 == pytest.approx(500, abs=20)


def test_long_headline_shrinks_to_stay_on_canvas():
    image = Image.new("RGB", (800, 320), (0, 0, 0))
    draw_headline(image, "A Really Quite Long Cover Title That Must Fit", (255, 255, 255))

    cols = np.asarray(image.convert("L")).max(axis=0)
    inked = np.flatnonzero(cols > 20)
    assert inked[0] >= 0
    assert inked[-1] <= 799


def test_empty_headline_draws_nothing():
    image = Image.new("RGB", (200, 100), (0, 0, 0))
    draw_headline(image, "   ", (255, 255, 255))
    assert np.asarray(image).max() == 0


def test_font_size_tracks_canvas_height():
    tall = Image.new("RGB", (2000, 800), (0, 0, 0))
    short = Image.new("RGB", (1000, 400), (0, 0, 0))
    draw_headline(tall, "Hxy", (255, 255, 255))
    draw_headline(short, "Hxy", (255, 255, 255))

    def ink_height(image):
        rows = np.asarray(image.convert("L")).max(axis=1)
        inked = np.flatnonzero(rows > 20)
        return inked[-1] - inked[0]

    assert ink_height(tall) == pytest.approx(2 * ink_height(short), rel=0.1)
    assert FONT_SIZE_RATIO > 0


# -- contrast --------------------------------------------------------------


def test_contrast_ratio_extremes():
    assert contrast_ratio((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0, abs=0.1)
    assert contrast_ratio((128, 128, 128), (128, 128, 128)) == pytest.approx(1.0)


def test_dark_ink_survives_a_pale_backdrop():
    assert pick_text_color((245, 245, 240), (9, 9, 11)) == (9, 9, 11)


def test_ink_flips_when_the_theme_colour_would_be_unreadable():
    """The forest palette on the light theme puts dark green under dark ink."""
    chosen = pick_text_color((45, 90, 70), (9, 9, 11))
    assert chosen == (250, 250, 250)
    assert contrast_ratio((45, 90, 70), chosen) >= 3.0


# -- engine ----------------------------------------------------------------


@pytest.mark.parametrize("style", sorted(STYLES))
def test_every_style_renders(classic, dark, style):
    image = render(spec(classic, dark, style=style))
    assert image.size == (SMALL.width, SMALL.height)
    assert image.mode == "RGB"


def test_render_is_deterministic_for_a_seed(classic, dark):
    a = render(spec(classic, dark))
    b = render(spec(classic, dark))
    assert a.tobytes() == b.tobytes()


def test_different_seeds_give_different_images(classic, dark):
    a = render(spec(classic, dark, seed=1))
    b = render(spec(classic, dark, seed=2))
    assert a.tobytes() != b.tobytes()


def test_render_without_text(classic, dark):
    assert render(spec(classic, dark, text=None)).size == (SMALL.width, SMALL.height)


def test_theme_changes_the_background(classic, registry):
    _, themes = registry
    dark_img = np.asarray(render(spec(classic, themes["dark"], text=None, style="linear")))
    light_img = np.asarray(render(spec(classic, themes["light"], text=None, style="linear")))
    assert dark_img.mean() != light_img.mean()


@pytest.mark.parametrize(
    ("fmt", "magic"), [("jpg", b"\xff\xd8"), ("png", b"\x89PNG"), ("webp", b"RIFF")]
)
def test_save_writes_each_format(classic, dark, tmp_path, fmt, magic):
    target = tmp_path / f"out.{fmt}"
    written = save(render(spec(classic, dark)), target, image_format=fmt, quality=90)
    assert written > 0
    assert target.read_bytes().startswith(magic)


def test_save_creates_missing_directories(classic, dark, tmp_path):
    target = tmp_path / "deep" / "nested" / "out.jpg"
    save(render(spec(classic, dark)), target, image_format="jpg", quality=90)
    assert target.is_file()


@pytest.mark.parametrize(
    "overrides",
    [{"image_format": "gif"}, {"grain": 1.5}, {"grain": -0.1}, {"quality": 0}, {"quality": 101}],
)
def test_invalid_specs_are_rejected(classic, dark, overrides):
    with pytest.raises(UsageError):
        spec(classic, dark, **overrides)


def test_grain_setting_reaches_the_output(classic, dark):
    smooth = np.asarray(render(spec(classic, dark, grain=0.0, text=None)), dtype=float)
    rough = np.asarray(render(spec(classic, dark, grain=1.0, text=None)), dtype=float)
    assert rough.std() > smooth.std()
