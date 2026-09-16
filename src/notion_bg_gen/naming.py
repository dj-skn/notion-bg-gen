"""Output filename construction.

The original picked a name by probing for ``page-N.png`` while the generator
wrote ``page-N.jpg`` (it rewrote the extension on the way out). The collision
check therefore never fired on the file it was about to write, and an existing
cover was silently replaced. Everything here works from the real extension, and
overwriting is opt-in.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

FALLBACK_STEM = "cover"
MAX_STEM_LENGTH = 60

_UNSAFE = re.compile(r"[^a-z0-9]+")
_WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def slugify(text: str | None, fallback: str = FALLBACK_STEM) -> str:
    """Turn a headline into a lowercase, hyphenated, filesystem-safe stem."""
    if not text or not text.strip():
        return fallback

    # Fold accents to ASCII so "Café Notes" becomes "cafe-notes", not "-notes".
    normalized = unicodedata.normalize("NFKD", text)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")

    slug = _UNSAFE.sub("-", ascii_only.lower()).strip("-")
    slug = slug[:MAX_STEM_LENGTH].strip("-")

    if not slug or slug in _WINDOWS_RESERVED:
        return fallback
    return slug


def unique_path(directory: Path, stem: str, extension: str, *, overwrite: bool = False) -> Path:
    """Return a free path in `directory`, probing the extension actually used.

    With `overwrite` the bare ``stem.ext`` is returned even if it exists; the
    caller has said it may clobber. Otherwise the first free ``stem-N.ext`` wins.
    """
    extension = extension.lstrip(".")
    candidate = directory / f"{stem}.{extension}"
    if overwrite or not candidate.exists():
        return candidate

    index = 2
    while True:
        candidate = directory / f"{stem}-{index}.{extension}"
        if not candidate.exists():
            return candidate
        index += 1
