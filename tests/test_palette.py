from __future__ import annotations

import pytest

from notion_bg_gen.errors import UsageError
from notion_bg_gen.render import palette as palette_mod


def test_builtin_palettes_load(registry):
    palettes, themes = registry
    assert "classic" in palettes
    assert {"dark", "light"} <= set(themes)


def test_every_palette_has_colours(registry):
    palettes, _ = registry
    for p in palettes.values():
        assert p.colors, f"{p.id} has no colours"
        for colour in p.colors:
            palette_mod.hex_to_rgb(colour)


def test_classic_keeps_its_light_specific_accents(classic):
    assert classic.colors_light is not None
    assert classic.for_theme("light") == classic.colors_light
    assert classic.for_theme("dark") == classic.colors


def test_palette_without_override_reuses_its_colours(registry):
    palettes, _ = registry
    ocean = palettes["ocean"]
    assert ocean.for_theme("light") == ocean.for_theme("dark")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("#1E90FF", (30, 144, 255)), ("1E90FF", (30, 144, 255)), ("#f0a", (255, 0, 170))],
)
def test_hex_to_rgb(raw, expected):
    assert palette_mod.hex_to_rgb(raw) == expected


@pytest.mark.parametrize("raw", ["#12345", "nope", "", "#gggggg"])
def test_hex_to_rgb_rejects_junk(raw):
    with pytest.raises(UsageError):
        palette_mod.hex_to_rgb(raw)


def test_unknown_palette_is_a_usage_error(registry):
    palettes, _ = registry
    with pytest.raises(UsageError, match="Unknown palette"):
        palette_mod.resolve_palette("nope", palettes)


def test_user_config_adds_a_palette(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(
        '[palettes.mine]\nname = "Mine"\ncolors = ["#000000", "#ffffff"]\n', encoding="utf-8"
    )
    palettes, _ = palette_mod.load(config)
    assert "mine" in palettes
    assert palettes["mine"].colors == ("#000000", "#ffffff")
    assert "classic" in palettes, "built-ins should still be present"


def test_user_config_can_override_a_builtin(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text('[palettes.classic]\ncolors = ["#000000"]\n', encoding="utf-8")
    palettes, _ = palette_mod.load(config)
    assert palettes["classic"].colors == ("#000000",)


def test_malformed_user_config_is_a_usage_error(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text("this is not = valid toml [[[", encoding="utf-8")
    with pytest.raises(UsageError):
        palette_mod.load(config)


def test_missing_user_config_is_fine(tmp_path):
    palettes, _ = palette_mod.load(tmp_path / "absent.toml")
    assert "classic" in palettes
