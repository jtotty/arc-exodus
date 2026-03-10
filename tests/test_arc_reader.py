from __future__ import annotations

from pathlib import Path

from arc_exodus.arc import default_sidebar_path, get_space_items, read_sidebar

ARC_FIXTURE = Path(__file__).parent / "fixtures" / "arc" / "sidebar.json"


class TestDefaultSidebarPath:
    def test_points_to_arc_sidebar_json(self) -> None:
        path = default_sidebar_path()
        assert path.name == "StorableSidebar.json"
        assert "Arc" in path.parts


class TestReadSidebar:
    def test_returns_arc_sidebar(self) -> None:
        sidebar = read_sidebar(ARC_FIXTURE)
        assert sidebar.spaces
        assert sidebar.items

    def test_parses_space_titles(self) -> None:
        sidebar = read_sidebar(ARC_FIXTURE)
        titles = [s.title for s in sidebar.spaces]
        assert "Personal" in titles

    def test_parses_items_as_dict_keyed_by_id(self) -> None:
        sidebar = read_sidebar(ARC_FIXTURE)
        for item_id, item in sidebar.items.items():
            assert item.id == item_id


class TestGetSpaceItems:
    def test_returns_space_items_for_named_space(self) -> None:
        sidebar = read_sidebar(ARC_FIXTURE)
        space_items = get_space_items(sidebar, "Personal")
        assert space_items.items

    def test_pinned_ids_are_populated(self) -> None:
        sidebar = read_sidebar(ARC_FIXTURE)
        space_items = get_space_items(sidebar, "Personal")
        assert space_items.pinned_ids

    def test_unpinned_ids_are_populated(self) -> None:
        sidebar = read_sidebar(ARC_FIXTURE)
        space_items = get_space_items(sidebar, "Personal")
        assert space_items.unpinned_ids

    def test_top_apps_ids_are_populated(self) -> None:
        sidebar = read_sidebar(ARC_FIXTURE)
        space_items = get_space_items(sidebar, "Personal")
        assert space_items.top_apps_ids

    def test_raises_for_unknown_space(self) -> None:
        import pytest

        sidebar = read_sidebar(ARC_FIXTURE)
        with pytest.raises(StopIteration):
            get_space_items(sidebar, "Nonexistent Space")
