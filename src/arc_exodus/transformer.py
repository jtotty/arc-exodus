"""Transform Arc bookmark data into Chrome bookmark format.

All functions in this module are pure:
- No file I/O
- No side effects
- Deterministic output for a given input

This makes them trivially testable and composable.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from arc_exodus.chrome.models import (
    BOOKMARK_BAR_ID,
    OTHER_ID,
    SYNCED_ID,
    ChromeBookmarkNode,
)
from arc_exodus.result import Ok

if TYPE_CHECKING:
    from arc_exodus.arc.models import ArcItem, SpaceItems

_SKIP_IDS = {"thebrowser.company.arcBasicsFolderID"}

_FIRST_USER_NODE_ID = max(int(BOOKMARK_BAR_ID), int(OTHER_ID), int(SYNCED_ID)) + 1

def transform_space(space_items: SpaceItems) -> Ok[list[ChromeBookmarkNode]]:
    """Transform a resolved Arc space into a list of Chrome bookmark nodes."""
    counter = _Counter(start=_FIRST_USER_NODE_ID)
    warnings: list[str] = []
    nodes: list[ChromeBookmarkNode] = []

    for item_id in space_items.top_apps_ids:
        node = _transform_item(item_id, space_items.items, counter, warnings)
        if node is not None:
            nodes.append(node)

    for item_id in space_items.pinned_ids:
        node = _transform_item(item_id, space_items.items, counter, warnings)
        if node is not None:
            nodes.append(node)

    for item_id in space_items.unpinned_ids:
        node = _transform_item(item_id, space_items.items, counter, warnings)
        if node is not None:
            nodes.append(node)

    return Ok(nodes, warnings=warnings)


def _transform_item(
    item_id: str,
    items: dict[str, ArcItem],
    counter: _Counter,
    warnings: list[str],
) -> ChromeBookmarkNode | None:
    """Return a Chrome node for the given Arc item, or None to skip it."""
    if item_id in _SKIP_IDS:
        return None

    item = items.get(item_id)
    if item is None:
        warnings.append(f"Skipped item '{item_id}': not found in items")
        return None

    return _build_node(item, items, counter, warnings)


def _build_node(
    item: ArcItem,
    items: dict[str, ArcItem],
    counter: _Counter,
    warnings: list[str],
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
            child_node = _transform_item(child_id, items, counter, warnings)
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

    warnings.append(f"Skipped item '{item.id}': unrecognised data shape")
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
