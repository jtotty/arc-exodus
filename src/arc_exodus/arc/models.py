"""Data models for Arc's sidebar schema."""

from __future__ import annotations

from dataclasses import dataclass
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

    top_apps_ids: list[str]   # children of any topApps container
    pinned_ids: list[str]     # children of the pinned container
    unpinned_ids: list[str]   # children of the unpinned container
    items: dict[str, ArcItem] # all items by id (superset — includes skipped items)
