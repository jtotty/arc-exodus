from __future__ import annotations

from arc_exodus.arc.models import ArcItem, SpaceItems
from arc_exodus.chrome.models import BOOKMARK_BAR_ID, OTHER_ID, SYNCED_ID
from arc_exodus.result import Ok
from arc_exodus.transformer import transform_space


def _tab_item(
    item_id: str,
    url: str,
    saved_title: str,
    created_at: float = 0.0,
    title: str | None = None,
) -> ArcItem:
    return ArcItem(
        id=item_id,
        title=title,
        children_ids=[],
        created_at=created_at,
        data={"tab": {"savedURL": url, "savedTitle": saved_title}},
    )


def _folder_item(
    item_id: str,
    title: str,
    children_ids: list[str],
    created_at: float = 0.0,
) -> ArcItem:
    return ArcItem(
        id=item_id,
        title=title,
        children_ids=children_ids,
        created_at=created_at,
        data={"list": {}},
    )


def _space_items(
    pinned: list[str] | None = None,
    unpinned: list[str] | None = None,
    top_apps: list[str] | None = None,
    items: dict[str, ArcItem] | None = None,
) -> SpaceItems:
    return SpaceItems(
        top_apps_ids=top_apps or [],
        pinned_ids=pinned or [],
        unpinned_ids=unpinned or [],
        items=items or {},
    )


class TestTransformSpace:
    def test_user_node_ids_do_not_collide_with_roots(self) -> None:
        item = _tab_item("a", "https://example.com", "Example")
        result = transform_space(_space_items(pinned=["a"], items={"a": item}))
        assert isinstance(result, Ok)
        assert result.value[0].id not in {BOOKMARK_BAR_ID, OTHER_ID, SYNCED_ID}

    def test_tab_item_becomes_url_node(self) -> None:
        item = _tab_item("a", "https://example.com", "Example")
        result = transform_space(_space_items(pinned=["a"], items={"a": item}))
        assert isinstance(result, Ok)
        node = result.value[0]
        assert node.node_type == "url"
        assert node.url == "https://example.com"

    def test_folder_item_becomes_folder_node(self) -> None:
        child = _tab_item("b", "https://example.com", "Example")
        folder = _folder_item("a", "My Folder", ["b"])
        items = {"a": folder, "b": child}
        result = transform_space(_space_items(pinned=["a"], items=items))
        assert isinstance(result, Ok)
        node = result.value[0]
        assert node.node_type == "folder"
        assert len(node.children) == 1

    def test_title_override_takes_precedence_over_saved_title(self) -> None:
        item = _tab_item("a", "https://example.com", "Saved Title", title="My Title")
        result = transform_space(_space_items(pinned=["a"], items={"a": item}))
        assert isinstance(result, Ok)
        assert result.value[0].name == "My Title"

    def test_saved_title_used_when_no_override(self) -> None:
        item = _tab_item("a", "https://example.com", "Saved Title")
        result = transform_space(_space_items(pinned=["a"], items={"a": item}))
        assert isinstance(result, Ok)
        assert result.value[0].name == "Saved Title"

    def test_timestamp_conversion(self) -> None:
        item = _tab_item("a", "https://example.com", "Example", created_at=0.0)
        result = transform_space(_space_items(pinned=["a"], items={"a": item}))
        assert isinstance(result, Ok)
        assert result.value[0].date_added == "12622780800000000"

    def test_skip_id_produces_no_node(self) -> None:
        result = transform_space(
            _space_items(pinned=["thebrowser.company.arcBasicsFolderID"])
        )
        assert isinstance(result, Ok)
        assert result.value == []
        assert result.warnings == []  # intentional skip — no warning

    def test_orphan_in_section_list_produces_warning(self) -> None:
        result = transform_space(_space_items(pinned=["nonexistent"]))
        assert isinstance(result, Ok)
        assert result.value == []
        assert any("nonexistent" in w for w in result.warnings)

    def test_orphan_in_folder_children_produces_warning(self) -> None:
        folder = _folder_item("a", "My Folder", ["missing"])
        result = transform_space(_space_items(pinned=["a"], items={"a": folder}))
        assert isinstance(result, Ok)
        assert len(result.value) == 1
        assert result.value[0].children == []
        assert any("missing" in w for w in result.warnings)

    def test_unknown_data_shape_produces_warning(self) -> None:
        item = ArcItem(
            id="a",
            title=None,
            children_ids=[],
            created_at=0.0,
            data={"unknown": {}},
        )
        result = transform_space(_space_items(pinned=["a"], items={"a": item}))
        assert isinstance(result, Ok)
        assert result.value == []
        assert any("a" in w for w in result.warnings)

    def test_top_apps_appear_before_pinned(self) -> None:
        top = _tab_item("top", "https://top.com", "Top")
        pinned = _tab_item("pin", "https://pin.com", "Pin")
        items = {"top": top, "pin": pinned}
        result = transform_space(
            _space_items(top_apps=["top"], pinned=["pin"], items=items)
        )
        assert isinstance(result, Ok)
        names = [n.name for n in result.value]
        assert names.index("Top") < names.index("Pin")
