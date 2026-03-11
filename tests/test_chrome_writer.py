from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from arc_exodus.chrome.errors import WriteError
from arc_exodus.chrome.messages import write_error_message
from arc_exodus.chrome.models import ChromeBookmarkNode
from arc_exodus.chrome.writer import write_bookmarks
from arc_exodus.result import Ok

if TYPE_CHECKING:
    from pathlib import Path


def _url_node(node_id: str, name: str, url: str) -> ChromeBookmarkNode:
    return ChromeBookmarkNode(
        id=node_id,
        name=name,
        node_type="url",
        guid="00000000-0000-4000-8000-000000000001",
        date_added="0",
        url=url,
    )


class TestWriteErrorMessage:
    def test_permission_denied_mentions_path(self) -> None:
        err = WriteError(kind="permission_denied", message="/some/path")
        assert "/some/path" in write_error_message(err)

    def test_disk_full_message(self) -> None:
        err = WriteError(kind="disk_full", message="")
        assert "disk" in write_error_message(err).lower()

    def test_unexpected_includes_detail(self) -> None:
        err = WriteError(kind="unexpected", message="something went wrong")
        assert "something went wrong" in write_error_message(err)


class TestFreshWrite:
    def test_returns_ok(self, tmp_path: Path) -> None:
        nodes = [_url_node("4", "Example", "https://example.com")]
        result = write_bookmarks(nodes, tmp_path)
        assert isinstance(result, Ok)

    def test_creates_bookmarks_file(self, tmp_path: Path) -> None:
        write_bookmarks([_url_node("4", "Example", "https://example.com")], tmp_path)
        assert (tmp_path / "Bookmarks").exists()

    def test_imported_from_arc_folder_in_bookmark_bar(self, tmp_path: Path) -> None:
        write_bookmarks([_url_node("4", "Example", "https://example.com")], tmp_path)
        data = json.loads((tmp_path / "Bookmarks").read_text())
        bar_children = data["roots"]["bookmark_bar"]["children"]
        names = [c["name"] for c in bar_children]
        assert "Imported from Arc" in names

    def test_imported_nodes_are_children_of_import_folder(self, tmp_path: Path) -> None:
        write_bookmarks([_url_node("4", "Example", "https://example.com")], tmp_path)
        data = json.loads((tmp_path / "Bookmarks").read_text())
        bar_children = data["roots"]["bookmark_bar"]["children"]
        folder = next(c for c in bar_children if c["name"] == "Imported from Arc")
        child_names = [c["name"] for c in folder["children"]]
        assert "Example" in child_names

    def test_checksum_is_valid(self, tmp_path: Path) -> None:
        from hashlib import md5

        write_bookmarks([_url_node("4", "Example", "https://example.com")], tmp_path)
        data = json.loads((tmp_path / "Bookmarks").read_text())
        digest = md5()

        def process(node: dict[str, Any]) -> None:
            digest.update(node["id"].encode("ascii"))
            digest.update(node["name"].encode("utf-16-le"))
            if node["type"] == "url":
                digest.update(b"url")
                digest.update(node["url"].encode("ascii"))
            else:
                digest.update(b"folder")
                for child in node.get("children", []):
                    process(child)

        process(data["roots"]["bookmark_bar"])
        process(data["roots"]["other"])
        process(data["roots"]["synced"])
        assert digest.hexdigest() == data["checksum"]
