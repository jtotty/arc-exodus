from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

from arc_exodus.cli import create_parser, main

ARC_FIXTURE = Path(__file__).parent / "fixtures" / "arc" / "sidebar.json"


class TestCreateParser:
    def test_creates_parser_with_program_name(self) -> None:
        parser = create_parser()
        assert parser.prog == "arc-exodus"

    def test_creates_parser_with_description(self) -> None:
        parser = create_parser()
        assert parser.description is not None

    def test_space_argument_is_optional(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["--profile", "/tmp"])
        assert args.space is None

    def test_profile_argument_is_optional(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["--space", "Personal"])
        assert args.profile is None


class TestMain:
    def _setup_chrome_dir(self, tmp_path: Path) -> Path:
        chrome_base = tmp_path / "Chrome"
        chrome_base.mkdir()
        default = chrome_base / "Default"
        default.mkdir()
        (default / "Preferences").write_text(json.dumps({"profile": {"name": "Test"}}))
        return chrome_base

    def test_writes_bookmarks_file_with_flags(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        profile_path = self._setup_chrome_dir(tmp_path) / "Default"
        monkeypatch.setattr("arc_exodus.cli.default_sidebar_path", lambda: ARC_FIXTURE)
        monkeypatch.setattr(sys, "argv", [
            "arc-exodus", "--space", "Personal", "--profile", str(profile_path),
        ])
        main()

        output = json.loads((profile_path / "Bookmarks").read_text())
        assert output["roots"]["bookmark_bar"]["children"]

    def test_writes_bookmarks_file_interactive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        chrome_base = self._setup_chrome_dir(tmp_path)
        monkeypatch.setattr("arc_exodus.cli.default_sidebar_path", lambda: ARC_FIXTURE)
        chrome_base_dir = "arc_exodus.cli.default_chrome_base_dir"
        monkeypatch.setattr(chrome_base_dir, lambda: chrome_base)
        monkeypatch.setattr(sys, "argv", ["arc-exodus"])
        inputs = iter(["1", "1"])
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
        main()

        assert (chrome_base / "Default" / "Bookmarks").exists()

    def test_prints_done(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        profile_path = self._setup_chrome_dir(tmp_path) / "Default"
        monkeypatch.setattr("arc_exodus.cli.default_sidebar_path", lambda: ARC_FIXTURE)
        monkeypatch.setattr(sys, "argv", [
            "arc-exodus", "--space", "Personal", "--profile", str(profile_path),
        ])
        main()
        assert "Done" in capsys.readouterr().out
