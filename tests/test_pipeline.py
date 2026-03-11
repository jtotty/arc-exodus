# pyright: basic
from __future__ import annotations

import json
from hashlib import md5
from pathlib import Path
from typing import Any

import pytest

from arc_exodus.arc import get_space_items, read_sidebar
from arc_exodus.chrome import write_bookmarks
from arc_exodus.transformer import make_chrome_bookmarks, transform_space

ARC_FIXTURE = Path(__file__).parent / "fixtures" / "arc" / "sidebar.json"


@pytest.fixture(scope="class")
def bookmark_bar(tmp_path_factory: pytest.TempPathFactory) -> Any:
    """Run the full pipeline once for the test class and return the bookmark bar."""
    from arc_exodus.result import Ok

    tmp_path = tmp_path_factory.mktemp("bookmarks")
    sidebar_result = read_sidebar(ARC_FIXTURE)
    assert isinstance(sidebar_result, Ok)
    space_result = get_space_items(sidebar_result.value, "Personal")
    assert isinstance(space_result, Ok)
    transform_result = transform_space(space_result.value)
    assert isinstance(transform_result, Ok)
    write_bookmarks(make_chrome_bookmarks(transform_result.value), tmp_path)
    return json.loads((tmp_path / "Bookmarks").read_text())


class TestPipeline:
    def test_included_items_appear_in_bookmark_bar(self, bookmark_bar: Any) -> None:
        names = [c["name"] for c in bookmark_bar["roots"]["bookmark_bar"]["children"]]

        assert "Google Calendar" in names
        assert "Dev Links" in names
        assert "My Custom Name" in names
        assert "Example Site" in names

    def test_skipped_items_are_absent(self, bookmark_bar: Any) -> None:
        def all_names(node: dict) -> list[str]:  # type: ignore[type-arg]
            names = [node["name"]]
            for child in node.get("children", []):
                names.extend(all_names(child))
            return names

        flat = all_names(bookmark_bar["roots"]["bookmark_bar"])
        assert "Arc Basics" not in flat
        assert "Getting Started" not in flat
        assert "Pull Requests" not in flat
        assert "PR #1" not in flat

    def test_dev_links_is_a_folder_with_correct_children(
        self, bookmark_bar: Any
    ) -> None:
        bar = bookmark_bar["roots"]["bookmark_bar"]
        dev_links = next(c for c in bar["children"] if c["name"] == "Dev Links")

        assert dev_links["type"] == "folder"
        child_names = [c["name"] for c in dev_links["children"]]
        assert "GitHub" in child_names
        assert "Figma" in child_names

    def test_custom_title_overrides_saved_title(self, bookmark_bar: Any) -> None:
        bar = bookmark_bar["roots"]["bookmark_bar"]
        custom = next(c for c in bar["children"] if c["name"] == "My Custom Name")

        assert custom["url"] == "https://notion.so"
        all_bar_names = [c["name"] for c in bar["children"]]
        assert "Notion \u2014 original title" not in all_bar_names

    def test_output_has_valid_checksum(self, bookmark_bar: Any) -> None:
        """Checksum must match the data — Chrome rejects the file otherwise."""
        roots = bookmark_bar["roots"]
        digest = md5()

        def process(node: dict) -> None:  # type: ignore[type-arg]
            digest.update(node["id"].encode("ascii"))
            digest.update(node["name"].encode("utf-16-le"))
            if node["type"] == "url":
                digest.update(b"url")
                digest.update(node["url"].encode("ascii"))
            else:
                digest.update(b"folder")
                for child in node.get("children", []):
                    process(child)

        process(roots["bookmark_bar"])
        process(roots["other"])
        process(roots["synced"])

        assert digest.hexdigest() == bookmark_bar["checksum"]

    def test_top_apps_appear_before_pinned_items(self, bookmark_bar: Any) -> None:
        names = [c["name"] for c in bookmark_bar["roots"]["bookmark_bar"]["children"]]

        assert "Google Calendar" in names, "Google Calendar (topApps) not found"
        assert "Dev Links" in names, "Dev Links (pinned) not found"
        assert names.index("Google Calendar") < names.index("Dev Links")
