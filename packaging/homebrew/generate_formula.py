"""Generate the Homebrew formula for a published release.

Usage:

    python packaging/homebrew/generate_formula.py 1.2.3 > Formula/notion-bg.rb

Run it against a version that is already on PyPI, then commit the output to
https://github.com/dj-skn/homebrew-tap.

The release workflow bumps the formula's URL and sha256 on its own, but it does
not touch the resource blocks. Regenerate with this script whenever a release
changes the dependency set.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

PROJECT = "notion-bg-gen"
PYTHON = "python@3.13"

# Taken from homebrew-core bottles rather than listed as resources. Homebrew
# installs resources with --no-binary=:all:, so leaving these as resources
# compiles numpy and Pillow from source - including a full CMake bootstrap -
# which turns a one-line install into a long build that also needs the Xcode
# command line tools. Both core formulae build for python@3.13, and the
# formula's virtualenv sees them through system site-packages.
BOTTLED = {"numpy": "numpy", "pillow": "pillow"}

TEST_BLOCK = """\
  test do
    assert_match version.to_s, shell_output("#{bin}/notion-bg --version")

    # Generating a cover exercises the bundled font and palette data, which is
    # what a broken install would most likely lose.
    system bin/"notion-bg", "generate", "Brew Test",
           "--size", "300x120", "--seed", "1", "--out", testpath, "--quiet"
    assert_path_exists testpath/"brew-test.jpg"

    # stdout must stay parseable; that is the contract scripts rely on.
    require "json"
    styles = JSON.parse(shell_output("#{bin}/notion-bg styles --json"))
    assert_includes styles["styles"].map { |s| s["id"] }, "mesh"
  end
"""


def sdist(name: str, version: str) -> tuple[str, str]:
    """Return the sdist URL and sha256 for an exact release on PyPI."""
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    with urllib.request.urlopen(url, timeout=30) as response:
        data = json.load(response)
    for entry in data["urls"]:
        if entry["packagetype"] == "sdist":
            return entry["url"], entry["digests"]["sha256"]
    raise SystemExit(f"No sdist published for {name} {version}.")


def resolve(version: str) -> list[tuple[str, str]]:
    """Install the release into a scratch venv and report what it pulled in."""
    with tempfile.TemporaryDirectory() as tmp:
        venv = Path(tmp) / "venv"
        python = venv / "bin" / "python"
        subprocess.run(["uv", "venv", "-q", str(venv), "--python", "3.13"], check=True)
        subprocess.run(
            ["uv", "pip", "install", "-q", "--python", str(python), f"{PROJECT}=={version}"],
            check=True,
        )
        listing = subprocess.run(
            ["uv", "pip", "list", "--python", str(python), "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
    return sorted(
        (pkg["name"], pkg["version"])
        for pkg in json.loads(listing.stdout)
        if pkg["name"] != PROJECT and pkg["name"].lower() not in BOTTLED
    )


def render(version: str) -> str:
    url, sha256 = sdist(PROJECT, version)

    # brew audit wants dependencies in alphabetical order.
    depends = "\n".join(f'  depends_on "{dep}"' for dep in sorted([*BOTTLED.values(), PYTHON]))

    resources = []
    for name, pinned in resolve(version):
        resource_url, resource_sha = sdist(name, pinned)
        resources.append(
            f'  resource "{name}" do\n'
            f'    url "{resource_url}"\n'
            f'    sha256 "{resource_sha}"\n'
            f"  end\n"
        )

    return (
        "class NotionBg < Formula\n"
        "  include Language::Python::Virtualenv\n"
        "\n"
        '  desc "Mesh-gradient cover images for Notion pages, from a terminal UI or a CLI"\n'
        '  homepage "https://github.com/dj-skn/notion-bg-gen"\n'
        f'  url "{url}"\n'
        f'  sha256 "{sha256}"\n'
        '  license "MIT"\n'
        '  head "https://github.com/dj-skn/notion-bg-gen.git", branch: "main"\n'
        "\n"
        f"{depends}\n"
        "\n" + "\n".join(resources) + "\n"
        "  def install\n"
        "    virtualenv_install_with_resources\n"
        "  end\n"
        "\n" + TEST_BLOCK + "end\n"
    )


def main() -> int:
    if len(sys.argv) != 2:
        sys.stderr.write(__doc__ or "")
        return 2
    sys.stdout.write(render(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
