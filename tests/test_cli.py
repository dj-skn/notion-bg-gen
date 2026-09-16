"""The command surface, including the contract that scripts and agents rely on."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from notion_bg_gen.cli import app

runner = CliRunner()

# Keep the test suite fast: every invocation renders at the smallest useful size.
SMALL = ["--size", "300x120"]


@pytest.fixture(autouse=True)
def _isolate_user_config(tmp_path, monkeypatch):
    """Never read or write the developer's real config during tests."""
    monkeypatch.setattr("notion_bg_gen.cli.config_path", lambda: tmp_path / "config.toml")


def run(*args, **kwargs):
    return runner.invoke(app, list(args), **kwargs)


# -- introspection ---------------------------------------------------------


def test_version():
    result = run("--version")
    assert result.exit_code == 0
    assert "notion-bg" in result.stdout


def test_help_lists_the_commands():
    result = run("--help")
    assert result.exit_code == 0
    for command in ("generate", "ui", "palettes", "styles", "config"):
        assert command in result.stdout


def test_palettes_json_is_machine_readable():
    result = run("palettes", "--json")
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    ids = {p["id"] for p in payload["palettes"]}
    assert "classic" in ids
    for entry in payload["palettes"]:
        assert entry["colors"]


def test_styles_json_is_machine_readable():
    result = run("styles", "--json")
    assert result.exit_code == 0
    ids = {s["id"] for s in json.loads(result.stdout)["styles"]}
    assert {"mesh", "aurora", "blobs", "linear"} <= ids


def test_palettes_table_renders():
    assert run("palettes").exit_code == 0


def test_styles_table_renders():
    assert run("styles").exit_code == 0


# -- generate --------------------------------------------------------------


def test_generate_writes_a_file(tmp_path):
    result = run("generate", "Hello", "-o", str(tmp_path), *SMALL)
    assert result.exit_code == 0
    assert (tmp_path / "hello.jpg").is_file()


def test_generate_without_text_uses_the_fallback_stem(tmp_path):
    assert run("generate", "-o", str(tmp_path), *SMALL).exit_code == 0
    assert (tmp_path / "cover.jpg").is_file()


def test_generate_json_contract(tmp_path):
    result = run("generate", "Hello", "-o", str(tmp_path), "--seed", "7", "--json", *SMALL)
    assert result.exit_code == 0

    payload = json.loads(result.stdout)
    assert payload["count"] == 1
    cover = payload["covers"][0]
    assert cover["seed"] == 7
    assert cover["text"] == "Hello"
    assert cover["palette"] == "classic"
    assert cover["theme"] == "dark"
    assert cover["style"] == "mesh"
    assert cover["written"] is True
    assert cover["bytes"] > 0
    assert cover["width"] == 300
    assert cover["height"] == 120


def test_json_stdout_carries_nothing_but_json(tmp_path):
    """An agent parses stdout directly, so progress chatter must go to stderr."""
    result = runner.invoke(
        app,
        ["generate", "Hello", "-o", str(tmp_path), "--json", *SMALL],
        catch_exceptions=False,
    )
    json.loads(result.stdout)


def test_count_produces_distinct_numbered_files(tmp_path):
    assert run("generate", "Note", "-n", "3", "-o", str(tmp_path), *SMALL).exit_code == 0
    assert {p.name for p in tmp_path.glob("*.jpg")} == {"note.jpg", "note-2.jpg", "note-3.jpg"}


def test_multiple_headlines(tmp_path):
    run("generate", "One", "Two", "-o", str(tmp_path), *SMALL)
    assert (tmp_path / "one.jpg").is_file()
    assert (tmp_path / "two.jpg").is_file()


def test_seed_makes_output_reproducible(tmp_path):
    run("generate", "A", "-o", str(tmp_path), "--seed", "5", "--name", "first", *SMALL)
    run("generate", "A", "-o", str(tmp_path), "--seed", "5", "--name", "second", *SMALL)
    assert (tmp_path / "first.jpg").read_bytes() == (tmp_path / "second.jpg").read_bytes()


def test_existing_file_is_not_overwritten(tmp_path):
    """Regression: the original clobbered an existing cover of the same name."""
    original = tmp_path / "hello.jpg"
    original.write_bytes(b"original bytes")

    run("generate", "Hello", "-o", str(tmp_path), *SMALL)

    assert original.read_bytes() == b"original bytes"
    assert (tmp_path / "hello-2.jpg").is_file()


def test_overwrite_flag_replaces_the_file(tmp_path):
    original = tmp_path / "hello.jpg"
    original.write_bytes(b"original bytes")
    run("generate", "Hello", "-o", str(tmp_path), "--overwrite", *SMALL)
    assert original.read_bytes() != b"original bytes"


def test_dry_run_writes_nothing_but_reports_distinct_paths(tmp_path):
    result = run("generate", "Note", "-n", "3", "-o", str(tmp_path), "--dry-run", "--json", *SMALL)
    assert result.exit_code == 0

    payload = json.loads(result.stdout)
    assert list(tmp_path.iterdir()) == []
    assert all(c["written"] is False for c in payload["covers"])
    assert len({c["path"] for c in payload["covers"]}) == 3


def test_from_file_skips_blanks_and_comments(tmp_path):
    listing = tmp_path / "titles.txt"
    listing.write_text("Alpha\n\n# skip me\nBeta\n", encoding="utf-8")

    result = run("generate", "--from-file", str(listing), "-o", str(tmp_path), "--json", *SMALL)
    payload = json.loads(result.stdout)

    assert [c["text"] for c in payload["covers"]] == ["Alpha", "Beta"]


def test_from_stdin(tmp_path):
    result = runner.invoke(
        app,
        ["generate", "--from-file", "-", "-o", str(tmp_path), "--json", *SMALL],
        input="Alpha\nBeta\n",
    )
    assert [c["text"] for c in json.loads(result.stdout)["covers"]] == ["Alpha", "Beta"]


@pytest.mark.parametrize("fmt", ["jpg", "png", "webp"])
def test_formats(tmp_path, fmt):
    run("generate", "Hi", "-o", str(tmp_path), "-f", fmt, *SMALL)
    assert (tmp_path / f"hi.{fmt}").is_file()


def test_custom_text_colour(tmp_path):
    assert (
        run("generate", "Hi", "-o", str(tmp_path), "--text-color", "#ff0000", *SMALL).exit_code == 0
    )


def test_quiet_suppresses_output(tmp_path):
    result = run("generate", "Hi", "-o", str(tmp_path), "--quiet", *SMALL)
    assert result.exit_code == 0
    assert result.stdout.strip() == ""


# -- failure modes ---------------------------------------------------------


@pytest.mark.parametrize(
    "args",
    [
        ("--palette", "nope"),
        ("--theme", "nope"),
        ("--style", "nope"),
        ("--size", "nope"),
        ("--format", "gif"),
        ("--text-color", "not-a-colour"),
        ("--font", "/nonexistent/font.ttf"),
    ],
)
def test_bad_input_exits_with_code_two(tmp_path, args):
    result = run("generate", "Hi", "-o", str(tmp_path), *args)
    assert result.exit_code == 2, result.output


def test_missing_from_file_exits_with_code_two(tmp_path):
    result = run("generate", "--from-file", str(tmp_path / "absent.txt"), "-o", str(tmp_path))
    assert result.exit_code == 2


def test_error_messages_name_the_valid_options(tmp_path):
    result = run("generate", "Hi", "-o", str(tmp_path), "--palette", "nope")
    assert "classic" in result.output


def test_out_of_range_options_are_rejected(tmp_path):
    assert run("generate", "Hi", "-o", str(tmp_path), "-n", "0").exit_code != 0
    assert run("generate", "Hi", "-o", str(tmp_path), "--grain", "5").exit_code != 0
    assert run("generate", "Hi", "-o", str(tmp_path), "--quality", "0").exit_code != 0


# -- config ----------------------------------------------------------------


def test_config_path_prints_a_path():
    result = run("config", "path")
    assert result.exit_code == 0
    assert "config.toml" in result.stdout


def test_config_show_without_a_file_is_not_an_error():
    assert run("config", "show").exit_code == 0
