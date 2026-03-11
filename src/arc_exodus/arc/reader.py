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

from arc_exodus.arc.errors import ReadError
from arc_exodus.arc.models import ArcItem, ArcSidebar, ArcSpace, SpaceItems
from arc_exodus.result import Err, Ok, Result


def default_sidebar_path() -> Path:
    """Return the default Arc sidebar path on macOS."""
    return (
        Path.home() / "Library" / "Application Support" / "Arc" / "StorableSidebar.json"
    )


def read_sidebar(path: Path) -> Result[ArcSidebar, ReadError]:
    """Read and parse Arc's StorableSidebar.json."""
    text_result = _read_text(path)
    if isinstance(text_result, Err):
        return text_result

    json_result = _parse_json(text_result.value)
    if isinstance(json_result, Err):
        return json_result

    container_result = _extract_container(json_result.value)
    if isinstance(container_result, Err):
        return container_result

    container = container_result.value
    warnings: list[str] = []

    spaces: list[ArcSpace] = []
    for obj in container["spaces_map"].values():
        if not isinstance(obj, dict):
            continue
        try:
            spaces.append(_parse_space(cast("dict[str, Any]", obj)))
        except (KeyError, IndexError, ValueError) as exc:
            warnings.append(f"Skipped unrecognised space entry: {exc}")

    items: dict[str, ArcItem] = {}
    for item_id, obj in container["items_map"].items():
        if not isinstance(obj, dict):
            continue
        try:
            items[item_id] = _parse_item(cast("dict[str, Any]", obj))
        except (KeyError, TypeError, ValueError) as exc:
            warnings.append(f"Skipped item '{item_id}': {exc}")

    return Ok(ArcSidebar(spaces=spaces, items=items), warnings=warnings)


def get_space_items(
    sidebar: ArcSidebar, space_title: str
) -> Result[SpaceItems, ReadError]:
    """Resolve the items belonging to the named space."""
    space: ArcSpace | None = None
    for s in sidebar.spaces:
        if s.title == space_title:
            space = s
            break
    if space is None:
        return Err(ReadError("space_not_found", f"No space named '{space_title}'"))

    try:
        pinned_container = sidebar.items[space.pinned_container_id]
        unpinned_container = sidebar.items[space.unpinned_container_id]
    except KeyError as exc:
        return Err(ReadError("invalid_structure", f"Missing container item: {exc}"))

    top_apps_ids: list[str] = []
    for item in sidebar.items.values():
        if "itemContainer" in item.data:
            container_type = item.data["itemContainer"]["containerType"]
            if "topApps" in container_type:
                top_apps_ids.extend(item.children_ids)

    return Ok(SpaceItems(
        top_apps_ids=top_apps_ids,
        pinned_ids=pinned_container.children_ids,
        unpinned_ids=unpinned_container.children_ids,
        items=sidebar.items,
    ))


def _read_text(path: Path) -> Result[str, ReadError]:
    try:
        return Ok(path.read_text())
    except PermissionError:
        return Err(ReadError("permission_denied", str(path)))
    except OSError:
        return Err(ReadError("file_not_found", str(path)))


def _parse_json(text: str) -> Result[dict[str, Any], ReadError]:
    try:
        return Ok(json.loads(text))
    except json.JSONDecodeError as exc:
        return Err(ReadError("malformed_json", str(exc)))


def _extract_container(raw: dict[str, Any]) -> Result[dict[str, Any], ReadError]:
    """Extract and pre-process the spaces/items maps from the raw sidebar dict."""
    try:
        container = raw["sidebar"]["containers"][1]
        spaces_raw: list[Any] = container["spaces"]
        items_raw: list[Any] = container["items"]
        spaces_map: dict[str, Any] = dict(
            zip(spaces_raw[::2], spaces_raw[1::2], strict=False)
        )
        items_map: dict[str, Any] = dict(
            zip(items_raw[::2], items_raw[1::2], strict=False)
        )
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        return Err(ReadError("invalid_structure", str(exc)))
    return Ok({"spaces_map": spaces_map, "items_map": items_map})


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
