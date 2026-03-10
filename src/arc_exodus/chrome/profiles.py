"""Discover Chrome profiles on the local filesystem."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def default_chrome_base_dir() -> Path:
    """Return the default Chrome profile base directory on macOS."""
    return Path.home() / "Library" / "Application Support" / "Google" / "Chrome"


def list_chrome_profiles(base_dir: Path) -> list[tuple[str, Path]]:
    """Return (display_name, path) pairs for each user Chrome profile in base_dir."""
    if not base_dir.is_dir():
        return []

    profiles: list[tuple[str, Path]] = []

    for entry in sorted(base_dir.iterdir()):
        if not re.fullmatch(r"Default|Profile \d+", entry.name):
            continue

        prefs = entry / "Preferences"
        if entry.is_dir() and prefs.exists():
            raw: Any = json.loads(prefs.read_text(encoding="utf-8"))
            name: str = str(raw["profile"]["name"])
            profiles.append((name, entry))

    return profiles
