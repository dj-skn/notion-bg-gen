"""Generate mesh-gradient cover images for Notion pages."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("notion-bg-gen")
except PackageNotFoundError:  # pragma: no cover - only hit from a bare checkout
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
