"""Transform Arc bookmark data into Chrome bookmark format.

All functions in this module are pure:
- No file I/O
- No side effects
- Deterministic output for a given input

This makes them trivially testable and composable.
"""

from __future__ import annotations

import uuid
from typing import Any

from arc_exodus.models import ArcItem, ChromeBookmarkNode, ChromeBookmarks, SpaceItems

_SKIP_IDS = {"thebrowser.company.arcBasicsFolderID"}

# Chrome's three root nodes have fixed GUIDs that are identical across all
# installations — they are hardcoded in the Chromium source, not generated
# per-profile. Chrome's checksum validation and sync depend on these values.
_BOOKMARK_BAR_GUID = "0bc5d13f-2cba-5d74-951f-3f233fe6c908"
_OTHER_GUID = "82b081ec-3dd3-529c-8475-ab6c344590dd"
_SYNCED_GUID = "4cf2e351-0e85-532b-bb37-df045d8f8d0f"


def transform_space(space_items: SpaceItems) -> ChromeBookmarks:
    """Transform a resolved Arc space into a Chrome bookmarks structure."""
    counter = _Counter(start=4)  # roots occupy ids 1-3

    bar_children: list[ChromeBookmarkNode] = []

    for item_id in space_items.top_apps_ids:
        node = _transform_item(item_id, space_items.items, counter)
        if node is not None:
            bar_children.append(node)

    for item_id in space_items.pinned_ids:
        node = _transform_item(item_id, space_items.items, counter)
        if node is not None:
            bar_children.append(node)

    for item_id in space_items.unpinned_ids:
        node = _transform_item(item_id, space_items.items, counter)
        if node is not None:
            bar_children.append(node)

    bookmark_bar = ChromeBookmarkNode(
        id="1",
        name="Bookmarks Bar",
        node_type="folder",
        guid=_BOOKMARK_BAR_GUID,
        date_added="0",
        children=bar_children,
        date_modified="0",
    )
    other = ChromeBookmarkNode(
        id="2",
        name="Other Bookmarks",
        node_type="folder",
        guid=_OTHER_GUID,
        date_added="0",
        date_modified="0",
    )
    synced = ChromeBookmarkNode(
        id="3",
        name="Mobile Bookmarks",
        node_type="folder",
        guid=_SYNCED_GUID,
        date_added="0",
        date_modified="0",
    )

    return ChromeBookmarks(bookmark_bar=bookmark_bar, other=other, synced=synced)


def _transform_item(
    item_id: str,
    items: dict[str, ArcItem],
    counter: _Counter,
) -> ChromeBookmarkNode | None:
    """Return a Chrome node for the given Arc item, or None to skip it."""
    if item_id in _SKIP_IDS:
        return None
    item = items.get(item_id)
    if item is None:
        return None
    return _build_node(item, items, counter)


def _build_node(
    item: ArcItem,
    items: dict[str, ArcItem],
    counter: _Counter,
) -> ChromeBookmarkNode | None:
    """Build a Chrome node from a validated Arc item, or None to skip it."""
    data = item.data

    if "welcomeToArc" in data or "itemContainer" in data:
        return None

    if "list" in data:
        list_data: dict[str, Any] = data["list"]
        if "automaticLiveFolderData" in list_data:
            return None
        children: list[ChromeBookmarkNode] = []
        for child_id in item.children_ids:
            child_node = _transform_item(child_id, items, counter)
            if child_node is not None:
                children.append(child_node)
        date_added = _arc_ts_to_chrome(item.created_at)
        return ChromeBookmarkNode(
            id=str(counter.next()),
            name=item.title or "",
            node_type="folder",
            guid=str(uuid.uuid4()),
            date_added=date_added,
            children=children,
            date_modified=date_added,
        )

    if "tab" in data:
        tab: dict[str, Any] = data["tab"]
        name = item.title if item.title is not None else str(tab["savedTitle"])
        return ChromeBookmarkNode(
            id=str(counter.next()),
            name=name,
            node_type="url",
            guid=str(uuid.uuid4()),
            date_added=_arc_ts_to_chrome(item.created_at),
            url=str(tab["savedURL"]),
        )

    return None


def _arc_ts_to_chrome(arc_ts: float) -> str:
    """Convert Arc CFAbsoluteTime to Chrome FILETIME microseconds."""
    return str(int((arc_ts + 12622780800) * 1_000_000))


class _Counter:
    """Simple integer counter for assigning sequential Chrome IDs."""

    def __init__(self, start: int) -> None:
        self._value = start

    def next(self) -> int:
        value = self._value
        self._value += 1
        return value
