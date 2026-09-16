# Configuration

The built-in palettes and themes can be extended, or replaced, with a TOML file
of your own.

## Finding the file

```bash
notion-bg config path
```

Typically:

| Platform | Path |
|---|---|
| macOS | `~/Library/Application Support/notion-bg-gen/config.toml` |
| Linux | `~/.config/notion-bg-gen/config.toml` |
| Windows | `%LOCALAPPDATA%\notion-bg-gen\config.toml` |

To create it and open it in your editor:

```bash
notion-bg config edit
```

## Adding a palette

```toml
[palettes.brand]
name = "Brand"
description = "Our colours."
colors = ["#0F172A", "#1E40AF", "#3B82F6", "#93C5FD", "#DBEAFE"]
```

```bash
notion-bg generate "Internal Docs" --palette brand
```

Seven to fifteen colours tends to look best with the `mesh` style; the others
are happy with fewer.

### Different colours on the light theme

Saturated colours that look right on a dark background often wash out on a light
one. `colors_light` overrides the accents when the light theme is selected:

```toml
[palettes.brand]
name = "Brand"
colors = ["#1E40AF", "#3B82F6", "#93C5FD"]
colors_light = ["#1E3A8A", "#2563EB", "#60A5FA"]
```

This is how the built-in `classic` palette works.

## Adding a theme

A theme sets the page background and the headline colour:

```toml
[themes.midnight]
background = "#020617"
text = "#E2E8F0"
```

```bash
notion-bg generate "Internal Docs" --palette brand --theme midnight
```

Any palette can pair with any theme.

## Overriding a built-in

Reusing a built-in id replaces it. This makes `classic` your own colours
everywhere, including as the default:

```toml
[palettes.classic]
name = "Classic"
colors = ["#000000", "#FFFFFF"]
```

Delete the entry to get the original back.

## Checking your work

```bash
notion-bg palettes
```

Your definitions appear alongside the built-ins. If the file has a syntax error
the tool says so and points at the line, rather than silently ignoring it.

## Colour format

Hex, with or without the leading `#`, in either the three or six digit form:
`#1E90FF`, `1E90FF` and `#f0a` are all valid.
