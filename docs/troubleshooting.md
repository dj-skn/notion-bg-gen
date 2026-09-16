# Troubleshooting

## "command not found: notion-bg"

The install worked but the location is not on your `PATH`.

```bash
uv tool update-shell      # if you installed with uv
pipx ensurepath           # if you installed with pipx
```

Close the terminal and open a new one afterwards. As a fallback, this always
works:

```bash
python -m notion_bg_gen --help
```

## macOS says the download "cannot be opened"

Expected for unsigned open-source binaries. Right-click the file in Finder,
choose **Open**, then confirm. Once only. Or:

```bash
xattr -d com.apple.quarantine ./notion-bg
```

Installing through Homebrew or uv avoids this entirely.

## The UI looks broken, or the preview is blank

The preview draws with half-block characters and 24-bit colour. Most modern
terminals handle this; a few do not.

- Check your terminal reports truecolor: `echo $COLORTERM` should print
  `truecolor` or `24bit`.
- Make the window bigger. Below roughly 60 columns there is not much to draw.
- If your terminal cannot manage it, the CLI produces identical images without
  needing any of this: `notion-bg generate "Title"`.

Known-good terminals: iTerm2, WezTerm, Kitty, Ghostty, Alacritty, Windows
Terminal, and the built-in terminals in VS Code and macOS.

## The UI will not open

If you see "Not a terminal, so the UI was not started", the command is running
somewhere without an interactive terminal - inside a pipe, a CI job, or some
editor consoles. That is deliberate. Use `notion-bg generate` instead.

## My headline is cut off, or smaller than expected

Long headlines shrink to fit the canvas. For a large title, use fewer words, or
a wider `--size`.

## The text is hard to read

The ink colour is chosen automatically against whatever the gradient put behind
it, but you can override it:

```bash
notion-bg generate "Title" --text-color "#ffffff"
```

Lowering `--grain` or switching to `--style linear` also helps, since both give
the text a calmer background.

## Files are bigger than I want

The default is a 3000 x 1200 JPEG at quality 92, which lands around 1 MB.

```bash
notion-bg generate "Title" --size cover --quality 80
```

That is roughly a quarter of the pixels and a smaller quality setting, and it
still meets Notion's documented minimum.

## Generation feels slow

A `cover@2x` render takes a second or two, mostly in the blur. `--size cover` is
about four times faster. `--style linear` is by far the cheapest style.

## My config file is being ignored

```bash
notion-bg config path     # is this the file you edited?
notion-bg palettes        # does your palette appear?
```

A malformed file produces an error rather than being skipped silently, so if
there is no error the file is being read. Check that the table is spelled
`[palettes.myname]`, and that `colors` is a list of strings.

## Something else

Open an issue with the output of `notion-bg --version`, the exact command you
ran, and the full error:
[github.com/dj-skn/notion-bg-gen/issues](https://github.com/dj-skn/notion-bg-gen/issues).
