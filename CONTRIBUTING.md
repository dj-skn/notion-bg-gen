# Contributing

Thanks for considering it. Bug reports, palette suggestions and pull requests
are all welcome.

## Getting set up

The project uses [uv](https://docs.astral.sh/uv/). With it installed:

```bash
git clone https://github.com/dj-skn/notion-bg-gen.git
cd notion-bg-gen
uv venv
uv pip install -e ".[dev]"
```

Or with plain pip:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Check it works:

```bash
notion-bg --version
notion-bg generate "Hello" --size cover
```

## The checks

CI runs these three, so run them before you push:

```bash
pytest                       # tests
ruff check . && ruff format --check .
mypy                         # strict
```

`pre-commit install` will run the lint and format steps for you on each commit.

## Working on the renderer

- Every style lives in `src/notion_bg_gen/render/gradient.py` and takes
  `(width, height, colors, rng)`, returning a colour field and its coverage mask.
  Adding one means writing the function, registering it in `STYLES`, and
  describing it in `STYLE_DESCRIPTIONS`.
- Rendering must stay deterministic for a given seed. Draw all randomness from
  the `rng` passed in, never from the `random` module or a fresh `default_rng()`.
  There is a test for this.
- Anything that changes how covers look should come with before and after images
  in the pull request.

## Adding a palette

Palettes live in `src/notion_bg_gen/data/palettes.toml`. Add a table, run
`notion-bg palettes` to see it, and generate a cover on both themes to check it
holds up. Seven to fifteen colours works well.

```toml
[palettes.example]
name = "Example"
description = "One short line, no trailing full stop needed."
colors = ["#123456", "#654321"]
```

## Commit messages

Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`)
keep the changelog easy to assemble, but this is a preference rather than a gate.

## Releasing

Maintainers only:

1. Update `version` in `pyproject.toml`.
2. Move the `Unreleased` entries in `CHANGELOG.md` under the new version.
3. Tag it: `git tag v1.2.3 && git push --tags`.

The release workflow builds the distributions, publishes to PyPI through trusted
publishing, builds the standalone binaries, attaches them to the GitHub release
and bumps the Homebrew formula.

The Homebrew bump only updates the formula's URL and sha256, not its dependency
pins. If a release changes dependencies, regenerate the formula once the version
is on PyPI and commit it to [homebrew-tap](https://github.com/dj-skn/homebrew-tap):

```bash
python packaging/homebrew/generate_formula.py 1.2.3 > ../homebrew-tap/Formula/notion-bg.rb
```

numpy and Pillow are deliberately Homebrew dependencies rather than resources;
the script explains why.
