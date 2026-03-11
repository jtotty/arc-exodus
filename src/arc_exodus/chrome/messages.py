"""Human-readable messages for Chrome writer errors."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arc_exodus.chrome.errors import WriteError


def write_error_message(error: WriteError) -> str:
    """Convert a WriteError into a human-readable CLI message."""
    if error.kind == "permission_denied":
        return (
            f"Error: Cannot write to Chrome profile at {error.message}.\n"
            "Check file permissions."
        )
    if error.kind == "disk_full":
        return "Error: Disk is full. Free up space and try again."
    return f"Error: {error.message}"
