"""User configuration: where it lives and what it may override."""

from __future__ import annotations

from pathlib import Path

from platformdirs import user_config_dir

APP_NAME = "notion-bg-gen"

CONFIG_TEMPLATE = """\
# notion-bg-gen configuration
#
# Anything defined here is merged over the built-in definitions, so reusing a
# built-in id (classic, ocean, dark, ...) overrides it. Run `notion-bg palettes`
# to see the result.

# [palettes.mine]
# name = "Mine"
# description = "Brand colours."
# colors = ["#0F172A", "#1E40AF", "#3B82F6", "#93C5FD"]
# # Optional: different accents when paired with the light theme.
# # colors_light = ["#1E40AF", "#3B82F6", "#93C5FD", "#DBEAFE"]

# [themes.midnight]
# background = "#020617"
# text = "#E2E8F0"
"""


def config_dir() -> Path:
    return Path(user_config_dir(APP_NAME, appauthor=False))


def config_path() -> Path:
    """The user's palettes/themes file. May not exist; that is not an error."""
    return config_dir() / "config.toml"


def ensure_config(path: Path | None = None) -> Path:
    """Create a commented starter config if none exists, and return its path."""
    target = path or config_path()
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(CONFIG_TEMPLATE, encoding="utf-8")
    return target
