from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from arc_exodus.arc import default_sidebar_path, get_space_items, read_sidebar
from arc_exodus.result import Err, Ok

ARC_FIXTURE = Path(__file__).parent / "fixtures" / "arc" / "sidebar.json"


class TestDefaultSidebarPath:
    def test_points_to_arc_sidebar_json(self) -> None:
        path = default_sidebar_path()
        assert path.name == "StorableSidebar.json"
        assert "Arc" in path.parts


class TestReadSidebar:
    def test_returns_ok_for_valid_file(self) -> None:
        result = read_sidebar(ARC_FIXTURE)
        assert isinstance(result, Ok)
        assert result.value.spaces
        assert result.value.items

    def test_parses_space_titles(self) -> None:
        result = read_sidebar(ARC_FIXTURE)
        assert isinstance(result, Ok)
        titles = [s.title for s in result.value.spaces]
        assert "Personal" in titles

    def test_parses_items_as_dict_keyed_by_id(self) -> None:
        result = read_sidebar(ARC_FIXTURE)
        assert isinstance(result, Ok)
        for item_id, item in result.value.items.items():
            assert item.id == item_id

    def test_returns_err_when_file_not_found(self) -> None:
        result = read_sidebar(Path("/nonexistent/path/sidebar.json"))
        assert isinstance(result, Err)
        assert result.error.kind == "file_not_found"

    def test_returns_err_for_malformed_json(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("not json {{{")
        result = read_sidebar(p)
        assert isinstance(result, Err)
        assert result.error.kind == "malformed_json"

    def test_returns_err_for_wrong_structure(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text('{"totally": "wrong"}')
        result = read_sidebar(p)
        assert isinstance(result, Err)
        assert result.error.kind == "invalid_structure"

    def test_warns_for_items_missing_required_fields(self, tmp_path: Path) -> None:
        # Build a minimal valid sidebar with one good item and one bad item
        # (bad item missing "id" and "createdAt")
        sidebar_data: dict[str, Any] = {
            "sidebar": {
                "containers": [
                    None,
                    {
                        "spaces": [],
                        "items": [
                            "good-item-id",
                            {
                                "id": "good-item-id",
                                "createdAt": 0.0,
                                "data": {},
                            },
                            "bad-item-id",
                            {
                                "title": "Missing required fields",
                                "data": {},
                            },
                        ],
                    },
                ]
            }
        }
        p = tmp_path / "sidebar.json"
        p.write_text(json.dumps(sidebar_data))
        result = read_sidebar(p)
        assert isinstance(result, Ok)
        assert "good-item-id" in result.value.items
        assert "bad-item-id" not in result.value.items
        assert len(result.warnings) == 1
        assert "bad-item-id" in result.warnings[0]

    def test_no_warnings_for_clean_fixture(self) -> None:
        result = read_sidebar(ARC_FIXTURE)
        assert isinstance(result, Ok)
        assert result.warnings == []


class TestGetSpaceItems:
    def test_returns_space_items_for_named_space(self) -> None:
        sidebar = read_sidebar(ARC_FIXTURE)
        assert isinstance(sidebar, Ok)
        result = get_space_items(sidebar.value, "Personal")
        assert isinstance(result, Ok)
        assert result.value.items

    def test_pinned_ids_are_populated(self) -> None:
        sidebar = read_sidebar(ARC_FIXTURE)
        assert isinstance(sidebar, Ok)
        result = get_space_items(sidebar.value, "Personal")
        assert isinstance(result, Ok)
        assert result.value.pinned_ids

    def test_unpinned_ids_are_populated(self) -> None:
        sidebar = read_sidebar(ARC_FIXTURE)
        assert isinstance(sidebar, Ok)
        result = get_space_items(sidebar.value, "Personal")
        assert isinstance(result, Ok)
        assert result.value.unpinned_ids

    def test_top_apps_ids_are_populated(self) -> None:
        sidebar = read_sidebar(ARC_FIXTURE)
        assert isinstance(sidebar, Ok)
        result = get_space_items(sidebar.value, "Personal")
        assert isinstance(result, Ok)
        assert result.value.top_apps_ids

    def test_returns_err_for_unknown_space(self) -> None:
        sidebar = read_sidebar(ARC_FIXTURE)
        assert isinstance(sidebar, Ok)
        result = get_space_items(sidebar.value, "Nonexistent Space")
        assert isinstance(result, Err)
        assert result.error.kind == "space_not_found"
        assert "Nonexistent Space" in result.error.message
