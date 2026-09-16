# Quickstart

## Your first cover

Run the tool with no arguments:

```bash
notion-bg
```

The terminal UI opens.

![The notion-bg terminal UI](assets/tui.svg)

1. Type a headline in the **Headline** field. Leave it empty for a cover with no text.
2. Use ++tab++ to move between fields, and the arrow keys to change a dropdown.
3. Press ++r++ to shuffle until you like the layout.
4. Press ++s++ to save.

The cover is written to a `covers/` folder in whatever directory you started
from. The status line tells you the exact path.

## Putting it on a Notion page

1. Open the Notion page.
2. Hover over the title and click **Add cover**.
3. Hover the cover, click **Change cover**, then **Upload**.
4. Choose the file from `covers/`.

## The same thing from the command line

```bash
notion-bg generate "Engineering Wiki"
```

Written to `covers/engineering-wiki.jpg`.

## A few useful variations

Try a different palette and style:

```bash
notion-bg generate "Roadmap" --palette ocean --style aurora
```

See what is available:

```bash
notion-bg palettes
notion-bg styles
```

Generate five versions and keep the one you like:

```bash
notion-bg generate "Design System" --count 5
```

Make a cover for every page in a list:

```bash
cat > titles.txt <<'LIST'
Engineering Wiki
Design System
Meeting Notes
LIST

notion-bg generate --from-file titles.txt
```

Get the same image back every time:

```bash
notion-bg generate "Roadmap" --seed 42
```

## Where things go

Covers land in `covers/` unless you pass `--out`. Existing files are never
replaced: a second `engineering-wiki.jpg` becomes `engineering-wiki-2.jpg`. Pass
`--overwrite` if you actually want to replace one.

## Next

- [CLI reference](cli.md) for every flag
- [Configuration](configuration.md) to add your own colours
