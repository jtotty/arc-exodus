"""Human-readable messages for Arc reader errors."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arc_exodus.arc.errors import ReadError


def read_error_message(error: ReadError) -> str:
    """Convert a ReadError into a human-readable CLI message."""
    if error.kind == "file_not_found":
        return (
            f"Error: Arc sidebar file not found at {error.message}.\n"
            "Is Arc installed and has it been run at least once?"
        )
    if error.kind == "permission_denied":
        return (
            f"Error: Cannot read Arc sidebar file at {error.message}.\n"
            "Check file permissions."
        )
    if error.kind == "malformed_json":
        return (
            "Error: Arc sidebar file is not valid JSON.\n"
            "Try restarting Arc to rebuild the file."
        )
    if error.kind == "invalid_structure":
        return (
            "Error: Arc sidebar file has an unexpected format.\n"
            f"Detail: {error.message}"
        )
    # space_not_found — message is already human-readable
    return f"Error: {error.message}"
