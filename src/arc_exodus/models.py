"""Data models for Arc and Chrome bookmark schemas.

Arc uses a flat list of items with parent-child ID references.
Chrome uses a nested tree structure.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ArcItem:
    """A single item from Arc's sidebar (tab, folder, container, etc.)."""

    id: str
    title: str | None
    children_ids: list[str]
    created_at: float
    data: dict[str, Any]


@dataclass(frozen=True)
class ArcSpace:
    """A space (profile) in Arc's sidebar."""

    id: str
    title: str
    pinned_container_id: str
    unpinned_container_id: str


@dataclass(frozen=True)
class ArcSidebar:
    """Parsed representation of Arc's StorableSidebar.json."""

    spaces: list[ArcSpace]
    items: dict[str, ArcItem]  # id → item


@dataclass(frozen=True)
class SpaceItems:
    """The resolved items for a single Arc space, ready for transformation.

    Produced by arc_reader, consumed by transformer.
    """

    top_apps_ids: list[str]  # children of any topApps container
    pinned_ids: list[str]  # children of the pinned container
    unpinned_ids: list[str]  # children of the unpinned container
    items: dict[str, ArcItem]  # all items by id (superset — includes skipped items)


@dataclass
class ChromeBookmarkNode:
    """A single node in Chrome's bookmark tree (url or folder)."""

    id: str
    name: str
    node_type: str  # "url" or "folder" — serialised as "type" in JSON
    guid: str
    date_added: str
    date_last_used: str = "0"
    url: str | None = None
    children: list[ChromeBookmarkNode] = field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]
    date_modified: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise to Chrome's JSON format."""
        d: dict[str, Any] = {
            "date_added": self.date_added,
            "date_last_used": self.date_last_used,
            "guid": self.guid,
            "id": self.id,
            "name": self.name,
            "type": self.node_type,
        }
        if self.node_type == "url":
            d["url"] = self.url
        else:
            d["children"] = [c.to_dict() for c in self.children]
            d["date_modified"] = self.date_modified or "0"
        return d


@dataclass
class ChromeBookmarks:
    """The top-level Chrome Bookmarks file structure."""

    bookmark_bar: ChromeBookmarkNode
    other: ChromeBookmarkNode
    synced: ChromeBookmarkNode
    checksum: str = ""
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Serialise to Chrome's JSON format."""
        return {
            "checksum": self.checksum,
            "roots": {
                "bookmark_bar": self.bookmark_bar.to_dict(),
                "other": self.other.to_dict(),
                "synced": self.synced.to_dict(),
            },
            "version": self.version,
        }
