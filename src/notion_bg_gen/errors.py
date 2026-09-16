"""Exception types that map onto the CLI's exit codes."""

from __future__ import annotations


class NotionBgError(Exception):
    """Base class for every error this tool raises deliberately.

    Carries the exit code the CLI should use, so command handlers can catch one
    type and still return the right status to a shell or a calling agent.
    """

    exit_code = 1

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class UsageError(NotionBgError):
    """The request was malformed: unknown palette, bad size, missing input."""

    exit_code = 2


class RenderError(NotionBgError):
    """Generation itself failed: unreadable font, unwritable output path."""

    exit_code = 1
