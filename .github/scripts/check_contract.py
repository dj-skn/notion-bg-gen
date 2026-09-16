"""Assert that the CLI's machine-readable output holds its shape.

Run by CI after generating a cover. This guards the contract that scripts and
agents depend on, which is easy to break without any test noticing.
"""

from __future__ import annotations

import json
import pathlib
import sys


def main() -> int:
    result = json.loads(pathlib.Path("result.json").read_text())
    assert result["count"] == 1, result

    cover = result["covers"][0]
    assert cover["seed"] == 1, cover
    assert cover["written"] is True, cover
    assert cover["text"] == "CI Smoke Test", cover
    assert cover["width"] == 1500 and cover["height"] == 600, cover
    assert cover["bytes"] > 0, cover
    assert pathlib.Path(cover["path"]).is_file(), cover

    palettes = json.loads(pathlib.Path("palettes.json").read_text())["palettes"]
    styles = json.loads(pathlib.Path("styles.json").read_text())["styles"]
    assert palettes, "no palettes listed"
    assert styles, "no styles listed"
    assert {s["id"] for s in styles} >= {"mesh", "aurora", "blobs", "linear"}, styles

    print(f"CLI contract OK: {cover['path']} ({cover['bytes']} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
