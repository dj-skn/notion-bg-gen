"""Filename construction, including the regression that motivated it."""

from __future__ import annotations

import pytest

from notion_bg_gen.naming import slugify, unique_path


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Engineering Wiki", "engineering-wiki"),
        ("  Spaced  Out  ", "spaced-out"),
        ("Café Notes", "cafe-notes"),
        ("Q4 / 2025 Roadmap!", "q4-2025-roadmap"),
        ("你好", "cover"),
        ("", "cover"),
        ("   ", "cover"),
        (None, "cover"),
        ("---", "cover"),
        ("CON", "cover"),
    ],
)
def test_slugify(raw, expected):
    assert slugify(raw) == expected


def test_slugify_truncates_long_input():
    assert len(slugify("word " * 100)) <= 60


def test_slugify_does_not_end_in_a_hyphen():
    assert not slugify("word " * 100).endswith("-")


def test_unique_path_uses_the_bare_name_when_free(tmp_path):
    assert unique_path(tmp_path, "page", "jpg") == tmp_path / "page.jpg"


def test_unique_path_numbers_around_an_existing_file(tmp_path):
    (tmp_path / "page.jpg").write_text("x")
    assert unique_path(tmp_path, "page", "jpg") == tmp_path / "page-2.jpg"


def test_unique_path_checks_the_extension_it_will_actually_write(tmp_path):
    """Regression: the collision check used to probe .png while writing .jpg.

    An existing cover was therefore never detected and was silently replaced.
    """
    existing = tmp_path / "page.jpg"
    existing.write_text("an existing cover")

    chosen = unique_path(tmp_path, "page", "jpg")

    assert chosen != existing
    assert existing.read_text() == "an existing cover"


def test_unique_path_overwrite_returns_the_taken_name(tmp_path):
    (tmp_path / "page.jpg").write_text("x")
    assert unique_path(tmp_path, "page", "jpg", overwrite=True) == tmp_path / "page.jpg"


def test_unique_path_skips_several_taken_names(tmp_path):
    for name in ("page.jpg", "page-2.jpg", "page-3.jpg"):
        (tmp_path / name).write_text("x")
    assert unique_path(tmp_path, "page", "jpg") == tmp_path / "page-4.jpg"


def test_unique_path_accepts_a_dotted_extension(tmp_path):
    assert unique_path(tmp_path, "page", ".png") == tmp_path / "page.png"
