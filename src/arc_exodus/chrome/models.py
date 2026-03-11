"""Data models for Chrome's bookmarks schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

BOOKMARK_BAR_ID = "1"
OTHER_ID = "2"
SYNCED_ID = "3"

# Fixed GUIDs hardcoded in the Chromium source — identical across all
# installations. Chrome's checksum validation and sync depend on these values.
BOOKMARK_BAR_GUID = "0bc5d13f-2cba-5d74-951f-3f233fe6c908"
OTHER_GUID = "82b081ec-3dd3-529c-8475-ab6c344590dd"
SYNCED_GUID = "4cf2e351-0e85-532b-bb37-df045d8f8d0f"


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
