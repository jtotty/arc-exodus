from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from arc_exodus.chrome import list_chrome_profiles


def _make_profile(base: Path, dir_name: str, display_name: str) -> Path:
    d = base / dir_name
    d.mkdir()
    (d / "Preferences").write_text(json.dumps({"profile": {"name": display_name}}))
    return d


class TestListChromeProfiles:
    def test_finds_default_profile(self, tmp_path: Path) -> None:
        default = _make_profile(tmp_path, "Default", "James")
        profiles = list_chrome_profiles(tmp_path)
        assert profiles == [("James", default)]

    def test_finds_numbered_profiles(self, tmp_path: Path) -> None:
        _make_profile(tmp_path, "Default", "James")
        _make_profile(tmp_path, "Profile 1", "Work")
        profiles = list_chrome_profiles(tmp_path)
        names = [name for name, _ in profiles]
        assert names == ["James", "Work"]

    def test_ignores_system_and_guest_profiles(self, tmp_path: Path) -> None:
        for dir_name in ("System Profile", "Guest Profile", "Crashpad", "SomeOtherDir"):
            _make_profile(tmp_path, dir_name, dir_name)
        assert list_chrome_profiles(tmp_path) == []

    def test_ignores_dirs_without_preferences(self, tmp_path: Path) -> None:
        (tmp_path / "Default").mkdir()
        assert list_chrome_profiles(tmp_path) == []

    def test_returns_empty_when_base_dir_missing(self, tmp_path: Path) -> None:
        assert list_chrome_profiles(tmp_path / "nonexistent") == []
