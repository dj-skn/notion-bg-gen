# Automation and agents

`notion-bg generate` is designed to be driven by something other than a person:
a shell script, a CI job, a Makefile, or an LLM agent with shell access.

## The contract

- **stdout is data, stderr is chatter.** With `--json`, stdout carries nothing
  but a single JSON object. Progress lines go to stderr, so a pipe stays clean.
- **Exit codes mean something.** `0` success, `1` render or write failure, `2`
  bad input. Nothing exits `0` after failing to write a file.
- **`--seed` makes output reproducible.** The same seed, palette, style, size and
  text produce byte-identical images.
- **Nothing is overwritten by default.** A name collision gets a numeric suffix
  unless you pass `--overwrite`.
- **Options are discoverable.** `palettes --json` and `styles --json` list the
  valid values, so a caller never has to guess or scrape `--help`.
- **The UI never opens by accident.** A bare `notion-bg` checks whether a real
  terminal is attached. In a pipe or a CI job it prints help and exits `2`.

## The JSON shape

```bash
notion-bg generate "Release Notes" --seed 42 --json
```

```json
{
  "covers": [
    {
      "path": "covers/release-notes.jpg",
      "text": "Release Notes",
      "seed": 42,
      "palette": "classic",
      "theme": "dark",
      "style": "mesh",
      "width": 3000,
      "height": 1200,
      "format": "jpg",
      "written": true,
      "bytes": 1137482
    }
  ],
  "count": 1
}
```

`covers` has one entry per generated image, in order. `written` is `false` under
`--dry-run`, and `bytes` is absent in that case.

## Recipes

### Check what would happen first

```bash
notion-bg generate --from-file titles.txt --dry-run --json
```

Writes nothing, but reports the exact paths, including how collisions would be
numbered.

### Get the path of what you just made

```bash
path=$(notion-bg generate "Weekly Notes" --json | jq -r '.covers[0].path')
open "$path"
```

### Generate a cover for every Markdown file in a directory

```bash
for file in content/*.md; do
  title=$(head -1 "$file" | sed 's/^# //')
  notion-bg generate "$title" --name "$(basename "$file" .md)" --out static/covers
done
```

### Fail a CI job if generation breaks

```bash
set -euo pipefail
notion-bg generate "Build ${GITHUB_SHA::7}" --seed 1 --json > cover.json
test -f "$(jq -r '.covers[0].path' cover.json)"
```

### Deterministic covers in a build

Seeding from something stable gives the same cover on every build, so the file
does not churn in version control:

```bash
seed=$(echo -n "$PAGE_SLUG" | cksum | cut -d' ' -f1)
notion-bg generate "$PAGE_TITLE" --seed "$seed" --overwrite --out static/covers
```

## Notes for agents

A minimal, reliable call looks like this:

```bash
notion-bg generate "TITLE" --seed 1 --json --out ./covers
```

- Read `--json` from stdout; ignore stderr unless the exit code is non-zero.
- Call `notion-bg palettes --json` and `notion-bg styles --json` to find valid
  values rather than guessing. An invalid value exits `2` and the error message
  lists the valid ones.
- Use `--dry-run` first when the caller cares about which paths get touched.
- Do not run bare `notion-bg` expecting output; it is the interactive UI.
- Rendering the default `cover@2x` size takes a second or two. `--size cover` is
  roughly four times faster if the result is only being previewed.

## Using it as a library

The renderer is importable if you would rather skip the subprocess:

```python
from pathlib import Path

from notion_bg_gen.render import palette
from notion_bg_gen.render.engine import CoverSpec, render, save
from notion_bg_gen.sizes import parse_size

palettes, themes = palette.load()

spec = CoverSpec(
    text="Engineering Wiki",
    palette=palettes["ocean"],
    theme=themes["dark"],
    size=parse_size("cover@2x"),
    style="aurora",
    seed=42,
)

save(render(spec), Path("cover.jpg"), image_format="jpg", quality=92)
```

`render` returns a Pillow `Image`, so you can composite or post-process it
before saving. `CoverSpec` validates its arguments on construction and raises
`notion_bg_gen.errors.UsageError` for anything invalid.
