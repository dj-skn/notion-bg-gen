from __future__ import annotations

import pytest

from notion_bg_gen.render import palette as palette_mod


@pytest.fixture()
def registry():
    """Built-in palettes and themes, with no user config merged in."""
    return palette_mod.load(None)


@pytest.fixture()
def classic(registry):
    palettes, _ = registry
    return palettes["classic"]


@pytest.fixture()
def dark(registry):
    _, themes = registry
    return themes["dark"]
