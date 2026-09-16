# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-09-16

The project becomes an installable tool with a terminal UI, a scriptable CLI,
and a test suite. Previously it was three scripts run from a git clone.

### Added

- **Terminal UI.** `notion-bg` with no arguments opens an interactive app with a
  live preview, built on Textual. The preview is the real renderer at a smaller
  size, so it matches what gets saved.
- **Scriptable CLI.** `notion-bg generate` with flags for every option, plus
  `palettes`, `styles` and `config` subcommands.
- **Installable package.** Published to PyPI, a Homebrew tap, and standalone
  binaries. Runs with `uvx notion-bg-gen` without installing anything.
- **Gradient styles.** `mesh` (the original look), `aurora`, `blobs` and `linear`,
  selected with `--style`.
- **Named palettes.** `classic`, `sunset`, `ocean`, `candy`, `forest`, `ember`,
  `lavender` and `mono`, selected with `--palette`. The original dark and light
  colour lists are preserved as `classic`.
- **User palettes and themes.** Define your own in a TOML config file; see
  `notion-bg config edit`.
- **Output control.** `--size` (named or `WIDTHxHEIGHT`), `--format` (jpg, png,
  webp), `--quality`, `--grain`, `--font` and `--text-color`.
- **Reproducibility.** `--seed` makes any cover byte-for-byte repeatable.
- **Batch generation.** Multiple headlines as arguments, `--count` for variations,
  and `--from-file` to read headlines from a file or stdin.
- **Machine-readable output.** `--json` on `generate`, `palettes` and `styles`,
  with human progress on stderr so stdout stays parseable. Exit codes are `0`
  success, `1` render failure, `2` bad input.
- **Automatic headline contrast.** The ink colour flips when a palette would
  otherwise put dark text on a dark field, measured with WCAG contrast ratios.
- Tests, type checking, linting and CI across Python 3.10 to 3.13 on Linux,
  macOS and Windows.

### Fixed

- **Covers could be silently overwritten.** The name chosen for a new cover was
  checked against a `.png` path while the file was written as `.jpg`, so an
  existing cover with the same name was never detected and was replaced without
  warning. Names are now checked against the extension actually written, and
  replacing a file requires `--overwrite`.
- **Grain blew out to white.** Noise was generated as a zero-centred normal
  distribution and then cast to `uint8`, which wraps negative samples instead of
  clamping them. About 47% of the "grain" landed between 200 and 255, producing
  salt-and-pepper speckle rather than a soft tooth. Noise is now applied as a
  signed delta in floating point and clipped once.
- **Headlines sat below centre.** Vertical centring discarded the top of the
  text bounding box, placing the headline roughly 15px low on a 1200px canvas.
- **Long headlines ran off the canvas.** They now shrink to fit.
- **Assets only resolved from the repository root.** The font and colour files
  were loaded from a relative `assets` path, so the tool broke when run from any
  other directory. They are now package data, resolved through
  `importlib.resources`.

### Changed

- Rendering is roughly an order of magnitude faster. The gradient was built from
  about 600 individually drawn PIL ellipses followed by a 300px Gaussian blur;
  it is now a vectorised numpy field with a three-pass box blur whose cost does
  not grow with the radius.
- Default JPEG quality is 92 rather than 100, which cuts file size substantially
  with no visible difference.
- Default output directory is `covers/` rather than `backgrounds/`.
- Output filenames are derived from the headline (`engineering-wiki.jpg`) rather
  than a `page-N` counter.
- Dependencies reduced to five direct packages. `halo` (unmaintained since 2020),
  `inquirer` and `colorama` were replaced by `typer`, `rich` and `textual`; the
  eight transitive pins that used to sit in `requirements.txt` are gone.
- Minimum Python is 3.10.

### Removed

- `main.py`, `gradient_generator.py`, `user_input_handler.py` and
  `requirements.txt`, replaced by the `notion_bg_gen` package and
  `pyproject.toml`.

[Unreleased]: https://github.com/dj-skn/notion-bg-gen/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/dj-skn/notion-bg-gen/releases/tag/v1.0.0
