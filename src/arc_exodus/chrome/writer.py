"""Write Chrome Bookmarks JSON file."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import shutil
import tempfile
import time
import uuid
from typing import TYPE_CHECKING, Any, Protocol

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
    existing = _read_existing(profile_path)
    if existing is not None:
        max_existing = max(
            _max_id(existing.bookmark_bar),
            _max_id(existing.other),
            _max_id(existing.synced),
        )
        import_folder = _make_import_folder(nodes, start_id=max_existing + 1)
        merged_bar = dataclasses.replace(
            existing.bookmark_bar,
            children=[*existing.bookmark_bar.children, import_folder],
        )
        bookmarks = ChromeBookmarks(
            bookmark_bar=merged_bar,
            other=existing.other,
            synced=existing.synced,
            version=existing.version,
        )
    else:
        import_folder = _make_import_folder(nodes, start_id=_FIRST_IMPORT_ID)
        bookmarks = _make_fresh_bookmarks(import_folder)

    bookmarks.checksum = _compute_checksum(bookmarks)
    output = json.dumps(bookmarks.to_dict(), indent=3, ensure_ascii=False)
    bookmarks_path = profile_path / "Bookmarks"
    if bookmarks_path.exists():
        shutil.copy2(bookmarks_path, profile_path / f"Bookmarks.bak.{int(time.time())}")
    _write_atomic(bookmarks_path, output)
    return Ok(None)


def _write_atomic(path: Path, content: str) -> None:
    """Write content to path atomically via a temp file in the same directory."""
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    os.write(fd, content.encode("utf-8"))
    os.close(fd)
    os.rename(tmp, path)


def _read_existing(profile_path: Path) -> ChromeBookmarks | None:
    """Read and parse an existing Bookmarks file, or return None if absent."""
    path = profile_path / "Bookmarks"
    if not path.exists():
        return None
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    roots = data["roots"]
    return ChromeBookmarks(
        bookmark_bar=_node_from_dict(roots["bookmark_bar"]),
        other=_node_from_dict(roots["other"]),
        synced=_node_from_dict(roots["synced"]),
        checksum=data.get("checksum", ""),
        version=data.get("version", 1),
    )


def _node_from_dict(d: dict[str, Any]) -> ChromeBookmarkNode:
    """Reconstruct a ChromeBookmarkNode from Chrome's JSON dict."""
    children = [_node_from_dict(c) for c in d.get("children", [])]
    return ChromeBookmarkNode(
        id=d["id"],
        name=d["name"],
        node_type=d["type"],
        guid=d["guid"],
        date_added=d["date_added"],
        date_last_used=d.get("date_last_used", "0"),
        url=d.get("url"),
        children=children,
        date_modified=d.get("date_modified"),
    )


def _max_id(node: ChromeBookmarkNode) -> int:
    """Return the maximum integer ID found in the node tree."""
    result = int(node.id)
    for child in node.children:
        result = max(result, _max_id(child))
    return result


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
                dataclasses.replace(node, id=str(node_id), children=new_children)
            )
        else:
            result.append(dataclasses.replace(node, id=str(node_id)))
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
