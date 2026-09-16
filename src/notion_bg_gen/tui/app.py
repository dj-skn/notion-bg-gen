"""The interactive terminal UI.

This is what a person gets when they type ``notion-bg`` with no arguments. It
drives exactly the same engine the CLI does, so whatever the preview shows is
what lands on disk - the preview is the real renderer at a smaller size, not an
approximation of it.
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any

from PIL import Image
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static

from ..config import config_path
from ..errors import NotionBgError
from ..naming import slugify, unique_path
from ..render import palette as palette_mod
from ..render.engine import MAX_SEED, CoverSpec, render, save
from ..render.gradient import DEFAULT_STYLE, STYLE_DESCRIPTIONS
from ..sizes import DEFAULT_SIZE, NAMED_SIZES, Size
from .preview import HalfBlockImage, fit_preview_pixels

DEFAULT_OUTPUT_DIR = Path("covers")
MAX_PREVIEW_ROWS = 24

# Preview renders at this width then downsamples into the half-block grid.
# Big enough for the headline to lay out properly, small enough to stay live.
PREVIEW_WORK_WIDTH = 640


class NotionBgApp(App[int]):
    """Pick a look, watch it update, save it."""

    CSS_PATH = "app.tcss"
    TITLE = "Notion Cover Generator"

    BINDINGS = [
        ("s", "save", "Save"),
        ("r", "shuffle", "Shuffle"),
        ("q", "quit", "Quit"),
        ("ctrl+s", "save", "Save"),
    ]

    def __init__(self, output_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
        super().__init__()
        self.output_dir = output_dir
        self.palettes, self.themes = palette_mod.load(config_path())
        self.seed = secrets.randbelow(MAX_SEED)
        self._last_saved: Path | None = None

    # -- layout ------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Horizontal(id="body"):
            with VerticalScroll(id="controls"):
                yield Label("Headline", classes="field-label-first")
                yield Input(placeholder="Leave empty for no text", id="text")

                yield Label("Theme", classes="field-label")
                yield Select(
                    [(t.title(), t) for t in sorted(self.themes)],
                    value="dark",
                    allow_blank=False,
                    id="theme",
                )

                yield Label("Palette", classes="field-label")
                yield Select(
                    [(p.name, p.id) for p in self.palettes.values()],
                    value="classic",
                    allow_blank=False,
                    id="palette",
                )

                yield Label("Style", classes="field-label")
                yield Select(
                    [(k.title(), k) for k in STYLE_DESCRIPTIONS],
                    value=DEFAULT_STYLE,
                    allow_blank=False,
                    id="style",
                )

                yield Label("Size", classes="field-label")
                yield Select(
                    [(f"{k}  ({v})", k) for k, v in NAMED_SIZES.items()],
                    value=DEFAULT_SIZE,
                    allow_blank=False,
                    id="size",
                )

                with Horizontal(id="actions"):
                    yield Button("Shuffle", variant="default", id="shuffle")
                    yield Button("Save", variant="primary", id="save")

            with Vertical(id="stage"):
                with Vertical(id="preview-frame"):
                    yield Static(id="preview")
                yield Static(id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_preview()

    # -- state -------------------------------------------------------------

    def _value(self, widget_id: str) -> Any:
        return self.query_one(f"#{widget_id}", Select).value

    def current_spec(self, size: Size) -> CoverSpec:
        """Build a spec from the controls, at whatever size is being asked for."""
        return CoverSpec(
            text=self.query_one("#text", Input).value.strip() or None,
            palette=self.palettes[self._value("palette")],
            theme=self.themes[self._value("theme")],
            size=size,
            style=self._value("style"),
            seed=self.seed,
        )

    def _target_size(self) -> Size:
        return NAMED_SIZES[self._value("size")]

    # -- preview -----------------------------------------------------------

    def refresh_preview(self) -> None:
        frame = self.query_one("#preview-frame")
        preview = self.query_one("#preview", Static)

        target = self._target_size()
        aspect = target.width / target.height

        # Leave room for the frame's border and padding.
        cells = max(16, frame.size.width - 6)
        rows = max(4, min(MAX_PREVIEW_ROWS, frame.size.height - 2))
        px_width, px_height = fit_preview_pixels(cells, aspect, rows)

        # Render at a working size and downsample, rather than rendering straight
        # into the cell grid. At ~60px wide the headline cannot shrink below its
        # minimum point size and would spill off the edge; this also means the
        # preview is a true scaled-down copy of the file that gets saved.
        work_width = max(px_width, PREVIEW_WORK_WIDTH)
        work_height = max(2, round(work_width / aspect))

        try:
            image = render(self.current_spec(Size(work_width, work_height)))
        except NotionBgError as exc:
            preview.update(f"[red]{exc.message}[/red]")
            return

        image = image.resize((px_width, px_height), Image.Resampling.LANCZOS)
        preview.update(HalfBlockImage(image))
        self._set_status(
            f"{target}  ·  seed {self.seed}  ·  {STYLE_DESCRIPTIONS[self._value('style')]}"
        )

    def _set_status(self, message: str, *, tone: str = "dim") -> None:
        self.query_one("#status", Static).update(f"[{tone}]{message}[/{tone}]")

    # -- events ------------------------------------------------------------

    def on_input_changed(self, _: Input.Changed) -> None:
        self.refresh_preview()

    def on_select_changed(self, _: Select.Changed) -> None:
        self.refresh_preview()

    def on_resize(self, _: Any) -> None:
        self.refresh_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "shuffle":
            self.action_shuffle()
        elif event.button.id == "save":
            self.action_save()

    # -- actions -----------------------------------------------------------

    def action_shuffle(self) -> None:
        """Draw a new seed, which is the only thing that changes the layout."""
        self.seed = secrets.randbelow(MAX_SEED)
        self.refresh_preview()

    def action_save(self) -> None:
        """Render at full resolution and write it out."""
        target_size = self._target_size()
        spec = self.current_spec(target_size)
        stem = slugify(self.query_one("#text", Input).value)
        path = unique_path(self.output_dir, stem, spec.image_format)

        self._set_status(f"Rendering {target_size}...")
        try:
            image = render(spec)
            written = save(image, path, image_format=spec.image_format, quality=spec.quality)
        except NotionBgError as exc:
            self._set_status(exc.message, tone="red")
            return

        self._last_saved = path
        self._set_status(f"Saved {path}  ({written / 1024:.0f} KB)", tone="green")
        self.notify(f"Saved {path}", title="Cover written", timeout=4)


def run_tui(output_dir: Path = DEFAULT_OUTPUT_DIR) -> int:
    """Run the app and return a process exit code."""
    app = NotionBgApp(output_dir=output_dir)
    app.run()
    return 0
