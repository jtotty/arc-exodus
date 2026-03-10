"""Read and parse Arc's StorableSidebar.json into domain models.

Responsible for:
- Locating the Arc sidebar file on disk
- Parsing JSON into ArcSidebar models
- Listing available spaces (profiles)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from arc_exodus.models import ArcItem, ArcSidebar, ArcSpace, SpaceItems


def default_sidebar_path() -> Path:
    """Return the default Arc sidebar path on macOS."""
    return (
        Path.home() / "Library" / "Application Support" / "Arc" / "StorableSidebar.json"
    )


def read_sidebar(path: Path) -> ArcSidebar:
    """Read and parse Arc's StorableSidebar.json."""
    raw: dict[str, Any] = json.loads(path.read_text())
    container = raw["sidebar"]["containers"][1]

    spaces_raw: list[Any] = container["spaces"]
    items_raw: list[Any] = container["items"]

    spaces_map: dict[str, Any] = dict(
        zip(spaces_raw[::2], spaces_raw[1::2], strict=False)
    )
    items_map: dict[str, Any] = dict(
        zip(items_raw[::2], items_raw[1::2], strict=False)
    )

    spaces = [
        _parse_space(cast("dict[str, Any]", obj))
        for obj in spaces_map.values()
        if isinstance(obj, dict)
    ]
    items = {
        item_id: _parse_item(cast("dict[str, Any]", obj))
        for item_id, obj in items_map.items()
        if isinstance(obj, dict)
    }

    return ArcSidebar(spaces=spaces, items=items)


def get_space_items(sidebar: ArcSidebar, space_title: str) -> SpaceItems:
    """Resolve the items belonging to the named space."""
    space = next(s for s in sidebar.spaces if s.title == space_title)

    pinned_container = sidebar.items[space.pinned_container_id]
    unpinned_container = sidebar.items[space.unpinned_container_id]

    top_apps_ids: list[str] = []
    for item in sidebar.items.values():
        if "itemContainer" in item.data:
            container_type = item.data["itemContainer"]["containerType"]
            if "topApps" in container_type:
                top_apps_ids.extend(item.children_ids)

    return SpaceItems(
        top_apps_ids=top_apps_ids,
        pinned_ids=pinned_container.children_ids,
        unpinned_ids=unpinned_container.children_ids,
        items=sidebar.items,
    )


def _parse_space(raw: dict[str, Any]) -> ArcSpace:
    container_ids: list[str] = raw["containerIDs"]
    pinned_idx = container_ids.index("pinned") + 1
    unpinned_idx = container_ids.index("unpinned") + 1
    return ArcSpace(
        id=raw["id"],
        title=raw["title"],
        pinned_container_id=container_ids[pinned_idx],
        unpinned_container_id=container_ids[unpinned_idx],
    )


def _parse_item(raw: dict[str, Any]) -> ArcItem:
    return ArcItem(
        id=raw["id"],
        title=raw.get("title"),
        children_ids=raw.get("childrenIds", []),
        created_at=raw["createdAt"],
        data=raw["data"],
    )
