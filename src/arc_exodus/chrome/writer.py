"""Write Chrome Bookmarks JSON file."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import TYPE_CHECKING, Protocol

from arc_exodus.chrome.models import (
    BOOKMARK_BAR_GUID,
    BOOKMARK_BAR_ID,
    OTHER_GUID,
    OTHER_ID,
    SYNCED_GUID,
    SYNCED_ID,
    ChromeBookmarkNode,
    ChromeBookmarks,
)
from arc_exodus.result import Ok, Result

if TYPE_CHECKING:
    from pathlib import Path

    from arc_exodus.chrome.errors import WriteError

_FIRST_IMPORT_ID = max(int(BOOKMARK_BAR_ID), int(OTHER_ID), int(SYNCED_ID)) + 1


class _Hasher(Protocol):
    """Minimal protocol for a hashlib digest object."""

    def update(self, data: bytes | bytearray | memoryview, /) -> None: ...


def write_bookmarks(
    nodes: list[ChromeBookmarkNode], profile_path: Path
) -> Result[None, WriteError]:
    """Construct root structure, compute checksum, and write Bookmarks."""
    import_folder = _make_import_folder(nodes, start_id=_FIRST_IMPORT_ID)
    bookmarks = _make_fresh_bookmarks(import_folder)
    bookmarks.checksum = _compute_checksum(bookmarks)
    output = json.dumps(bookmarks.to_dict(), indent=3, ensure_ascii=False)
    (profile_path / "Bookmarks").write_text(output, encoding="utf-8")
    return Ok(None)


def _make_import_folder(
    nodes: list[ChromeBookmarkNode], start_id: int
) -> ChromeBookmarkNode:
    """Wrap nodes in an 'Imported from Arc' folder with sequential IDs."""
    reassigned, _ = _reassign_ids(nodes, start_id + 1)
    return ChromeBookmarkNode(
        id=str(start_id),
        name="Imported from Arc",
        node_type="folder",
        guid=str(uuid.uuid4()),
        date_added="0",
        children=reassigned,
        date_modified="0",
    )


def _reassign_ids(
    nodes: list[ChromeBookmarkNode], start: int
) -> tuple[list[ChromeBookmarkNode], int]:
    """Return nodes with IDs reassigned sequentially (DFS pre-order)."""
    result: list[ChromeBookmarkNode] = []
    current = start
    for node in nodes:
        node_id = current
        current += 1
        if node.node_type == "folder":
            new_children, current = _reassign_ids(node.children, current)
            result.append(
                ChromeBookmarkNode(
                    id=str(node_id),
                    name=node.name,
                    node_type=node.node_type,
                    guid=node.guid,
                    date_added=node.date_added,
                    date_last_used=node.date_last_used,
                    children=new_children,
                    date_modified=node.date_modified,
                )
            )
        else:
            result.append(
                ChromeBookmarkNode(
                    id=str(node_id),
                    name=node.name,
                    node_type=node.node_type,
                    guid=node.guid,
                    date_added=node.date_added,
                    date_last_used=node.date_last_used,
                    url=node.url,
                )
            )
    return result, current


def _make_fresh_bookmarks(import_folder: ChromeBookmarkNode) -> ChromeBookmarks:
    """Build an empty root structure with the import folder in bookmark_bar."""
    bookmark_bar = ChromeBookmarkNode(
        id=BOOKMARK_BAR_ID,
        name="Bookmarks Bar",
        node_type="folder",
        guid=BOOKMARK_BAR_GUID,
        date_added="0",
        children=[import_folder],
        date_modified="0",
    )
    other = ChromeBookmarkNode(
        id=OTHER_ID,
        name="Other Bookmarks",
        node_type="folder",
        guid=OTHER_GUID,
        date_added="0",
        date_modified="0",
    )
    synced = ChromeBookmarkNode(
        id=SYNCED_ID,
        name="Mobile Bookmarks",
        node_type="folder",
        guid=SYNCED_GUID,
        date_added="0",
        date_modified="0",
    )
    return ChromeBookmarks(bookmark_bar=bookmark_bar, other=other, synced=synced)


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
