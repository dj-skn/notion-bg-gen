"""Palette and theme loading.

Built-in definitions ship inside the package and are read through
``importlib.resources``, not a relative path, so they resolve identically
whether the tool was installed with pipx, run via uvx, frozen into a binary or
executed from a git checkout.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from ..errors import UsageError

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised on 3.10 only
    import tomli as tomllib

RGB = tuple[int, int, int]


@dataclass(frozen=True)
class Palette:
    """A named set of accent colours used to build the gradient field."""

    id: str
    name: str
    description: str
    colors: tuple[str, ...]
    colors_light: tuple[str, ...] | None = None

    def for_theme(self, theme_id: str) -> tuple[str, ...]:
        """Accent colours for a theme, honouring a light-specific override."""
        if theme_id == "light" and self.colors_light:
            return self.colors_light
        return self.colors

    def rgb_for_theme(self, theme_id: str) -> list[RGB]:
        return [hex_to_rgb(c) for c in self.for_theme(theme_id)]


@dataclass(frozen=True)
class Theme:
    """Page background and headline colour."""

    id: str
    background: str
    text: str

    @property
    def background_rgb(self) -> RGB:
        return hex_to_rgb(self.background)

    @property
    def text_rgb(self) -> RGB:
        return hex_to_rgb(self.text)


def hex_to_rgb(value: str) -> RGB:
    """Convert ``#rrggbb`` (or the 3-digit short form) to an RGB triple."""
    raw = value.strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        raise UsageError(
            f"{value!r} is not a valid hex colour.", hint="Expected a form like #1E90FF."
        )
    try:
        return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))
    except ValueError:
        raise UsageError(
            f"{value!r} is not a valid hex colour.", hint="Expected a form like #1E90FF."
        ) from None


def _parse(data: dict[str, Any]) -> tuple[dict[str, Palette], dict[str, Theme]]:
    palettes: dict[str, Palette] = {}
    for pid, raw in (data.get("palettes") or {}).items():
        colors = tuple(raw.get("colors") or ())
        if not colors:
            raise UsageError(f"Palette {pid!r} defines no colours.")
        light = raw.get("colors_light")
        palettes[pid] = Palette(
            id=pid,
            name=raw.get("name", pid.replace("-", " ").title()),
            description=raw.get("description", ""),
            colors=colors,
            colors_light=tuple(light) if light else None,
        )

    themes: dict[str, Theme] = {}
    for tid, raw in (data.get("themes") or {}).items():
        themes[tid] = Theme(id=tid, background=raw["background"], text=raw["text"])
    return palettes, themes


def _load_builtin() -> tuple[dict[str, Palette], dict[str, Theme]]:
    source = resources.files("notion_bg_gen.data").joinpath("palettes.toml")
    return _parse(tomllib.loads(source.read_text(encoding="utf-8")))


def load(user_config: Path | None = None) -> tuple[dict[str, Palette], dict[str, Theme]]:
    """Return built-in palettes and themes, with a user file merged over them."""
    palettes, themes = _load_builtin()
    if user_config and user_config.is_file():
        try:
            extra = tomllib.loads(user_config.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise UsageError(
                f"Could not parse {user_config}: {exc}",
                hint="Run `notion-bg config edit` to fix the file, or delete it to start over.",
            ) from None
        user_palettes, user_themes = _parse(extra)
        palettes.update(user_palettes)
        themes.update(user_themes)
    return palettes, themes


def resolve_palette(palette_id: str, palettes: dict[str, Palette]) -> Palette:
    if palette_id not in palettes:
        known = ", ".join(sorted(palettes))
        raise UsageError(
            f"Unknown palette {palette_id!r}.",
            hint=f"Run `notion-bg palettes` to see them all. Available: {known}",
        )
    return palettes[palette_id]


def resolve_theme(theme_id: str, themes: dict[str, Theme]) -> Theme:
    if theme_id not in themes:
        known = ", ".join(sorted(themes))
        raise UsageError(f"Unknown theme {theme_id!r}.", hint=f"Available: {known}")
    return themes[theme_id]
