"""Write Chrome Bookmarks JSON file."""

from __future__ import annotations

import contextlib
import dataclasses
import errno
import hashlib
import json
import os
import shutil
import tempfile
import time
import uuid
from typing import TYPE_CHECKING, Any, Protocol

from arc_exodus.chrome.errors import WriteError
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
from arc_exodus.result import Err, Ok, Result

if TYPE_CHECKING:
    from pathlib import Path

_FIRST_IMPORT_ID = max(int(BOOKMARK_BAR_ID), int(OTHER_ID), int(SYNCED_ID)) + 1


class _Hasher(Protocol):
    """Minimal protocol for a hashlib digest object."""

    def update(self, data: bytes | bytearray | memoryview, /) -> None: ...


def write_bookmarks(
    nodes: list[ChromeBookmarkNode], profile_path: Path
) -> Result[None, WriteError]:
    """Construct root structure, compute checksum, and write Bookmarks."""
    existing_result = _read_existing(profile_path)
    if isinstance(existing_result, Err):
        return existing_result

    existing = existing_result.value
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
    return _write_atomic(profile_path, output)


def _read_existing(
    profile_path: Path,
) -> Result[ChromeBookmarks | None, WriteError]:
    """Read and parse an existing Bookmarks file, or return Ok(None) if absent."""
    path = profile_path / "Bookmarks"
    try:
        if not path.exists():
            return Ok(None)
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except PermissionError as exc:
        return Err(WriteError(kind="permission_denied", message=str(exc)))
    except OSError as exc:
        return Err(WriteError(kind="unexpected", message=str(exc)))
    roots = data["roots"]
    return Ok(
        ChromeBookmarks(
            bookmark_bar=_node_from_dict(roots["bookmark_bar"]),
            other=_node_from_dict(roots["other"]),
            synced=_node_from_dict(roots["synced"]),
            checksum=data.get("checksum", ""),
            version=data.get("version", 1),
        )
    )


def _write_atomic(profile_path: Path, content: str) -> Result[None, WriteError]:
    """Back up existing file (if any) and write content atomically."""
    bookmarks_path = profile_path / "Bookmarks"
    tmp_path: str | None = None
    try:
        if bookmarks_path.exists():
            bak = profile_path / f"Bookmarks.bak.{int(time.time())}"
            shutil.copy2(bookmarks_path, bak)
        fd, tmp_path = tempfile.mkstemp(dir=profile_path)
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        os.rename(tmp_path, bookmarks_path)
        return Ok(None)
    except PermissionError as exc:
        if tmp_path is not None:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
        return Err(WriteError(kind="permission_denied", message=str(exc)))
    except OSError as exc:
        if tmp_path is not None:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
        if exc.errno == errno.ENOSPC:
            return Err(WriteError(kind="disk_full", message=""))
        return Err(WriteError(kind="unexpected", message=str(exc)))


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
