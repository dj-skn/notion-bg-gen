"""Command line interface.

Two audiences share one engine. A person who types ``notion-bg`` and nothing
else gets the terminal UI. A script or an agent gets explicit subcommands,
``--json`` on stdout, real exit codes, and ``--seed`` for reproducibility.

The one rule that keeps both honest: the UI only ever launches when stdout is a
real terminal. Piped, redirected or run in CI, a bare invocation prints help and
exits 2 rather than trying to open a full-screen app nobody can see.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table
from typer.core import TyperGroup

from . import __version__
from .config import config_path, ensure_config
from .errors import NotionBgError, UsageError
from .naming import slugify, unique_path
from .render import palette as palette_mod
from .render.engine import DEFAULT_FORMAT, DEFAULT_QUALITY, FORMATS, CoverSpec, render, save
from .render.gradient import DEFAULT_STYLE, STYLE_DESCRIPTIONS, STYLES
from .render.grain import DEFAULT_GRAIN
from .sizes import DEFAULT_SIZE, NAMED_SIZES, parse_size

DEFAULT_OUTPUT_DIR = Path("covers")

# Human-facing output goes to stderr so that --json owns stdout completely.
err = Console(stderr=True)
out = Console()


def emit_data(text: str) -> None:
    """Write machine-consumable or verbatim text to stdout, untouched.

    Deliberately not Rich. Rich colourises when FORCE_COLOR is set (CI runners
    commonly set it), soft-wraps at the terminal width, and interprets square
    brackets as markup - which silently swallowed TOML table headers such as
    `[palettes.brand]` in `config show`. Any of those turn valid output into
    something a caller cannot parse or a person cannot trust.
    """
    sys.stdout.write(text if text.endswith("\n") else text + "\n")


def emit_json(payload: object) -> None:
    """Write a JSON document to stdout and nothing else."""
    emit_data(json.dumps(payload, indent=2))


class ErrorHandlingGroup(TyperGroup):
    """Turn our exceptions into tidy messages and exit codes.

    This lives on the group rather than in ``main()`` so that every entry point
    behaves the same: the console script, ``python -m notion_bg_gen``, and any
    test or embedder that invokes the Typer app directly.
    """

    def invoke(self, ctx: Any) -> Any:
        try:
            return super().invoke(ctx)
        except NotionBgError as exc:
            err.print(f"[red]Error:[/red] {exc.message}")
            if exc.hint:
                err.print(f"[dim]{exc.hint}[/dim]")
            raise SystemExit(exc.exit_code) from None


app = typer.Typer(
    cls=ErrorHandlingGroup,
    name="notion-bg",
    help="Generate mesh-gradient cover images for Notion pages.",
    add_completion=True,
    no_args_is_help=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"notion-bg {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def cli(
    ctx: typer.Context,
    _version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """Generate mesh-gradient cover images for Notion pages."""
    if ctx.invoked_subcommand is not None:
        return

    # No subcommand: hand a person the UI, hand everything else the help text.
    if sys.stdout.isatty() and sys.stdin.isatty():
        from .tui.app import run_tui

        raise typer.Exit(run_tui())

    err.print("[dim]Not a terminal, so the UI was not started.[/dim]")
    err.print(ctx.get_help())
    raise typer.Exit(2)


@app.command()
def ui() -> None:
    """Open the interactive terminal UI."""
    from .tui.app import run_tui

    raise typer.Exit(run_tui())


@app.command(name="generate")
def generate(
    texts: list[str] | None = typer.Argument(
        None,
        metavar="[TEXT]...",
        help="Headline for each cover. Omit for a textless cover.",
    ),
    count: int = typer.Option(
        1, "--count", "-n", min=1, max=500, help="Covers to make per headline."
    ),
    palette: str = typer.Option(
        "classic", "--palette", "-p", help="Palette id. See `notion-bg palettes`."
    ),
    theme: str = typer.Option("dark", "--theme", "-t", help="Theme id: dark or light."),
    style: str = typer.Option(
        DEFAULT_STYLE, "--style", "-s", help="Gradient style. See `notion-bg styles`."
    ),
    size: str = typer.Option(DEFAULT_SIZE, "--size", help="Named size or WIDTHxHEIGHT."),
    output_dir: Path = typer.Option(
        DEFAULT_OUTPUT_DIR, "--out", "-o", help="Directory to write into."
    ),
    image_format: str = typer.Option(DEFAULT_FORMAT, "--format", "-f", help="jpg, png or webp."),
    quality: int = typer.Option(
        DEFAULT_QUALITY, "--quality", "-q", min=1, max=100, help="JPEG/WebP quality."
    ),
    grain: float = typer.Option(
        DEFAULT_GRAIN, "--grain", "-g", min=0.0, max=1.0, help="Film grain, 0 to 1."
    ),
    seed: int | None = typer.Option(None, "--seed", help="Seed for reproducible output."),
    font: Path | None = typer.Option(
        None, "--font", help="Path to a .ttf or .otf to use instead of Inter."
    ),
    text_color: str | None = typer.Option(
        None,
        "--text-color",
        help="Force a headline colour. Default picks one that stays readable.",
    ),
    from_file: Path | None = typer.Option(
        None,
        "--from-file",
        help="Read one headline per line from a file ('-' for stdin).",
    ),
    name: str | None = typer.Option(
        None, "--name", help="Filename stem. Default is a slug of the headline."
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Replace an existing file instead of numbering."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Report what would be written without writing it."
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit a JSON result on stdout."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress progress output."),
) -> None:
    """Generate one or more covers.

    [bold]Examples[/bold]

      notion-bg generate "Engineering Wiki"
      notion-bg generate "Roadmap" --palette ocean --style aurora
      notion-bg generate --from-file titles.txt --seed 7 --json
    """
    headlines = list(texts or [])
    if from_file:
        headlines.extend(_read_headlines(from_file))
    if not headlines:
        headlines = [""]

    palettes, themes = palette_mod.load(config_path())
    chosen_palette = palette_mod.resolve_palette(palette, palettes)
    chosen_theme = palette_mod.resolve_theme(theme, themes)
    if style not in STYLES:
        raise UsageError(f"Unknown style {style!r}.", hint=f"Available styles: {', '.join(STYLES)}")
    if image_format not in FORMATS:
        raise UsageError(
            f"Unknown format {image_format!r}.", hint=f"Available formats: {', '.join(FORMATS)}"
        )
    resolved_size = parse_size(size)
    ink = palette_mod.hex_to_rgb(text_color) if text_color else None
    if font and not font.is_file():
        raise UsageError(f"No font file at {font}.")

    results: list[dict[str, object]] = []
    # unique_path only sees the filesystem, and a dry run writes nothing, so
    # track what this invocation has already claimed.
    reserved: set[Path] = set()
    total = len(headlines) * count
    show_progress = not quiet and not as_json

    index = 0
    for headline in headlines:
        for _variant in range(count):
            index += 1
            # Offsetting by the variant keeps --seed reproducible while still
            # giving each cover in a batch a different field.
            cover_seed = seed + index - 1 if seed is not None else None
            spec_kwargs = {
                "text": headline or None,
                "palette": chosen_palette,
                "theme": chosen_theme,
                "size": resolved_size,
                "style": style,
                "grain": grain,
                "font": font,
                "text_color": ink,
                "image_format": image_format,
                "quality": quality,
            }
            spec = (
                CoverSpec(seed=cover_seed, **spec_kwargs)  # type: ignore[arg-type]
                if cover_seed is not None
                else CoverSpec(**spec_kwargs)  # type: ignore[arg-type]
            )

            stem = name or slugify(headline)
            target = unique_path(output_dir, stem, image_format, overwrite=overwrite)
            while not overwrite and target in reserved:
                target = unique_path(output_dir, f"{stem}-{len(reserved) + 1}", image_format)
            reserved.add(target)

            record: dict[str, object] = {
                "path": str(target),
                "text": headline or None,
                "seed": spec.seed,
                "palette": chosen_palette.id,
                "theme": chosen_theme.id,
                "style": style,
                "width": resolved_size.width,
                "height": resolved_size.height,
                "format": image_format,
            }

            if dry_run:
                record["written"] = False
                results.append(record)
                if show_progress:
                    err.print(f"[dim]would write[/dim] {target}")
                continue

            if show_progress:
                label = headline or "(no text)"
                err.print(f"[dim]{index}/{total}[/dim] {label} [dim]->[/dim] {target}")

            image = render(spec)
            written = save(image, target, image_format=image_format, quality=quality)
            record["written"] = True
            record["bytes"] = written
            results.append(record)

    if as_json:
        emit_json({"covers": results, "count": len(results)})
    elif not quiet:
        verb = "Would generate" if dry_run else "Generated"
        err.print(f"[green]{verb} {len(results)} cover(s)[/green] in [bold]{output_dir}[/bold]")


@app.command()
def palettes(
    as_json: bool = typer.Option(False, "--json", help="Emit JSON on stdout."),
) -> None:
    """List available palettes."""
    registry, _ = palette_mod.load(config_path())
    if as_json:
        payload = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "colors": list(p.colors),
                "colors_light": list(p.colors_light) if p.colors_light else None,
            }
            for p in registry.values()
        ]
        emit_json({"palettes": payload})
        return

    table = Table(title="Palettes", title_justify="left", header_style="bold")
    table.add_column("id", style="cyan", no_wrap=True)
    table.add_column("name")
    table.add_column("swatch", no_wrap=True)
    table.add_column("description", style="dim")
    for p in registry.values():
        swatch = "".join(f"[{c}]█[/{c}]" for c in p.colors[:8])
        table.add_row(p.id, p.name, swatch, p.description)
    out.print(table)


@app.command()
def styles(
    as_json: bool = typer.Option(False, "--json", help="Emit JSON on stdout."),
) -> None:
    """List available gradient styles."""
    if as_json:
        payload = [{"id": k, "description": v} for k, v in STYLE_DESCRIPTIONS.items()]
        emit_json({"styles": payload})
        return

    table = Table(title="Styles", title_justify="left", header_style="bold")
    table.add_column("id", style="cyan", no_wrap=True)
    table.add_column("description", style="dim")
    for key, description in STYLE_DESCRIPTIONS.items():
        table.add_row(key, description)
    out.print(table)

    sizes = Table(title="\nSizes", title_justify="left", header_style="bold")
    sizes.add_column("id", style="cyan", no_wrap=True)
    sizes.add_column("pixels", style="dim")
    for key, value in NAMED_SIZES.items():
        suffix = "  (default)" if key == DEFAULT_SIZE else ""
        sizes.add_row(key, f"{value}{suffix}")
    out.print(sizes)


config_app = typer.Typer(cls=ErrorHandlingGroup, help="Inspect and edit your palette overrides.")
app.add_typer(config_app, name="config")


@config_app.command("path")
def config_path_cmd() -> None:
    """Print the path to the config file."""
    emit_data(str(config_path()))


@config_app.command("show")
def config_show() -> None:
    """Print the contents of the config file."""
    path = config_path()
    if not path.is_file():
        err.print(f"[dim]No config yet at {path}. Run `notion-bg config edit` to create one.[/dim]")
        raise typer.Exit(0)
    emit_data(path.read_text(encoding="utf-8"))


@config_app.command("edit")
def config_edit() -> None:
    """Create the config file if needed, then open it in $EDITOR."""
    path = ensure_config()
    err.print(f"[dim]{path}[/dim]")
    typer.launch(str(path), locate=False)


def _read_headlines(source: Path) -> list[str]:
    """Read one headline per line, skipping blanks and # comments."""
    if str(source) == "-":
        raw = sys.stdin.read()
    else:
        if not source.is_file():
            raise UsageError(f"No such file: {source}")
        raw = source.read_text(encoding="utf-8")
    return [
        line.strip()
        for line in raw.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def main() -> None:
    """Console-script entry point.

    Errors are handled by ErrorHandlingGroup; this only adds the Ctrl-C path,
    which has to sit outside Click's own invocation.
    """
    try:
        app()
    except KeyboardInterrupt:  # pragma: no cover - needs a real terminal
        err.print("\n[dim]Cancelled.[/dim]")
        raise SystemExit(130) from None
