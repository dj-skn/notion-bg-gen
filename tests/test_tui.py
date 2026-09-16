"""The terminal UI. Driven headlessly through Textual's test pilot."""

from __future__ import annotations

import pytest
from textual.widgets import Input, Select

from notion_bg_gen.sizes import NAMED_SIZES
from notion_bg_gen.tui.app import NotionBgApp
from notion_bg_gen.tui.preview import fit_preview_pixels

TERMINAL = (110, 32)


@pytest.fixture()
def app(tmp_path):
    return NotionBgApp(output_dir=tmp_path)


@pytest.mark.asyncio
async def test_app_starts_and_renders_a_preview(app):
    async with app.run_test(size=TERMINAL) as pilot:
        await pilot.pause()
        assert app.query_one("#preview")


@pytest.mark.asyncio
async def test_typing_a_headline_refreshes_the_preview(app):
    async with app.run_test(size=TERMINAL) as pilot:
        await pilot.pause()
        app.query_one("#text", Input).value = "Engineering Wiki"
        await pilot.pause()
        assert app.current_spec(NAMED_SIZES["cover"]).text == "Engineering Wiki"


@pytest.mark.asyncio
async def test_shuffle_changes_the_seed(app):
    async with app.run_test(size=TERMINAL) as pilot:
        await pilot.pause()
        before = app.seed
        await pilot.press("r")
        await pilot.pause()
        assert app.seed != before


@pytest.mark.asyncio
async def test_switching_style_and_palette(app):
    async with app.run_test(size=TERMINAL) as pilot:
        await pilot.pause()
        app.query_one("#style", Select).value = "aurora"
        app.query_one("#palette", Select).value = "ocean"
        await pilot.pause()

        spec = app.current_spec(NAMED_SIZES["cover"])
        assert spec.style == "aurora"
        assert spec.palette.id == "ocean"


@pytest.mark.asyncio
async def test_saving_writes_a_file(app, tmp_path):
    async with app.run_test(size=TERMINAL) as pilot:
        await pilot.pause()
        app.query_one("#text", Input).value = "Saved Cover"
        app.query_one("#size", Select).value = "square"
        await pilot.pause()
        app.action_save()
        await pilot.pause()

        written = list(tmp_path.glob("*.jpg"))
        assert [p.name for p in written] == ["saved-cover.jpg"]


@pytest.mark.asyncio
async def test_saving_twice_does_not_overwrite(app, tmp_path):
    async with app.run_test(size=TERMINAL) as pilot:
        await pilot.pause()
        app.query_one("#text", Input).value = "Twice"
        app.query_one("#size", Select).value = "square"
        await pilot.pause()
        app.action_save()
        await pilot.pause()
        app.action_save()
        await pilot.pause()

        assert {p.name for p in tmp_path.glob("*.jpg")} == {"twice.jpg", "twice-2.jpg"}


@pytest.mark.asyncio
async def test_preview_survives_a_narrow_terminal(app):
    async with app.run_test(size=(40, 16)) as pilot:
        await pilot.pause()
        app.refresh_preview()
        await pilot.pause()


def test_preview_fits_within_the_row_budget():
    for aspect in (2.5, 1.0, 3.2):
        _width, height = fit_preview_pixels(120, aspect, 10)
        assert height / 2 <= 10
        assert height % 2 == 0


def test_preview_keeps_the_cover_aspect_ratio():
    width, height = fit_preview_pixels(100, 2.5, 40)
    assert width / height == pytest.approx(2.5, abs=0.15)
