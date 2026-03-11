from __future__ import annotations

from arc_exodus.arc.errors import ReadError


class TestReadError:
    def test_has_kind_and_message(self) -> None:
        err = ReadError(kind="file_not_found", message="no such file")
        assert err.kind == "file_not_found"
        assert err.message == "no such file"

    def test_all_kinds_are_constructable(self) -> None:
        kinds = [
            "file_not_found",
            "permission_denied",
            "malformed_json",
            "invalid_structure",
            "space_not_found",
        ]
        for kind in kinds:
            err = ReadError(kind=kind, message="test")  # type: ignore[arg-type]
            assert err.kind == kind
