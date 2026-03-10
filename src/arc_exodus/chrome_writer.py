"""Write Chrome Bookmarks JSON file.

Responsible for:
- Serializing Chrome bookmark models to JSON
- Writing to the correct Chrome profile directory
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from arc_exodus.models import ChromeBookmarkNode, ChromeBookmarks


class _Hasher(Protocol):
    """Minimal protocol for a hashlib digest object."""

    def update(self, data: bytes | bytearray | memoryview, /) -> None: ...


def write_bookmarks(bookmarks: ChromeBookmarks, profile_path: Path) -> None:
    """Compute checksum and write Bookmarks to the Chrome profile directory."""
    bookmarks.checksum = _compute_checksum(bookmarks)
    output = json.dumps(bookmarks.to_dict(), indent=3, ensure_ascii=False)
    (profile_path / "Bookmarks").write_text(output, encoding="utf-8")


def _compute_checksum(bookmarks: ChromeBookmarks) -> str:
    """Compute the MD5 checksum Chrome uses to validate the Bookmarks file."""
    digest = hashlib.md5()
    _process_node(bookmarks.bookmark_bar, digest)
    _process_node(bookmarks.other, digest)
    _process_node(bookmarks.synced, digest)
    return digest.hexdigest()


def _process_node(node: ChromeBookmarkNode, digest: _Hasher) -> None:
    digest.update(node.id.encode("ascii"))
    digest.update(node.name.encode("utf-16-le"))
    if node.node_type == "url":
        digest.update(b"url")
        digest.update((node.url or "").encode("ascii"))
    else:
        digest.update(b"folder")
        for child in node.children:
            _process_node(child, digest)
