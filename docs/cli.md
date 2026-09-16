# CLI reference

Run `notion-bg --help`, or `notion-bg <command> --help`, for the same
information in your terminal.

## `notion-bg`

With no arguments and a real terminal attached, this opens the
[terminal UI](quickstart.md).

In a pipe, a redirect or a CI job there is no terminal to draw on, so it prints
help and exits `2` instead. That makes it safe to call from a script without
risking a hung full-screen app.

| Option | Description |
|---|---|
| `--version`, `-V` | Print the version and exit |
| `--help`, `-h` | Show help |
| `--install-completion` | Install shell completion |

## `notion-bg generate [TEXT]...`

Generate one or more covers. Each `TEXT` argument is a headline; omit them all
for a cover with no text.

```bash
notion-bg generate "Engineering Wiki"
notion-bg generate "Alpha" "Beta" "Gamma"
notion-bg generate --from-file titles.txt --seed 7
```

### Appearance

| Option | Default | Description |
|---|---|---|
| `--palette`, `-p` | `classic` | Palette id. See [`palettes`](#notion-bg-palettes) |
| `--theme`, `-t` | `dark` | `dark` or `light`, plus any you define |
| `--style`, `-s` | `mesh` | `mesh`, `aurora`, `blobs` or `linear` |
| `--grain`, `-g` | `0.35` | Film grain from `0` to `1` |
| `--font` | bundled Inter Bold | Path to a `.ttf` or `.otf` |
| `--text-color` | automatic | Hex colour for the headline |

The headline colour is chosen automatically to stay readable against whatever
the gradient put behind it, measured with WCAG contrast ratios. `--text-color`
overrides that.

### Output

| Option | Default | Description |
|---|---|---|
| `--out`, `-o` | `covers` | Directory to write into, created if missing |
| `--name` | slug of the headline | Filename stem |
| `--size` | `cover@2x` | Named size or `WIDTHxHEIGHT` |
| `--format`, `-f` | `jpg` | `jpg`, `png` or `webp` |
| `--quality`, `-q` | `92` | Quality for `jpg` and `webp` |
| `--overwrite` | off | Replace an existing file instead of numbering |

Named sizes:

| Name | Pixels |
|---|---|
| `cover` | 1500 x 600 |
| `cover@2x` | 3000 x 1200 (default) |
| `wide` | 3840 x 1200 |
| `square` | 1200 x 1200 |

Custom sizes accept `2000x800`, between 64 and 10000 pixels a side.

### Batching

| Option | Default | Description |
|---|---|---|
| `--count`, `-n` | `1` | Covers per headline, up to 500 |
| `--from-file` | - | Read one headline per line; `-` reads stdin |
| `--seed` | random | Reproducible output. A batch increments from it |

Blank lines and lines starting with `#` in a `--from-file` list are skipped.

### Behaviour

| Option | Description |
|---|---|
| `--json` | Structured result on stdout |
| `--dry-run` | Report the paths that would be written, write nothing |
| `--quiet` | Suppress progress output |

## `notion-bg palettes`

List available palettes, including any you defined yourself.

```bash
notion-bg palettes
notion-bg palettes --json
```

## `notion-bg styles`

List gradient styles and named sizes.

```bash
notion-bg styles
notion-bg styles --json
```

## `notion-bg config`

| Command | Description |
|---|---|
| `notion-bg config path` | Print the path to the config file |
| `notion-bg config show` | Print its contents |
| `notion-bg config edit` | Create it if needed and open it in `$EDITOR` |

See [Configuration](configuration.md).

## `notion-bg ui`

Open the terminal UI explicitly. Identical to running `notion-bg` bare, but it
does not fall back to help when there is no terminal.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Rendering or writing failed |
| `2` | Bad input: unknown palette, style, size or format; missing file |
| `130` | Interrupted with ++ctrl+c++ |
