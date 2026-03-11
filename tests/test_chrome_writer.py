from __future__ import annotations

from arc_exodus.chrome.errors import WriteError
from arc_exodus.chrome.messages import write_error_message


class TestWriteErrorMessage:
    def test_permission_denied_mentions_path(self) -> None:
        err = WriteError(kind="permission_denied", message="/some/path")
        assert "/some/path" in write_error_message(err)

    def test_disk_full_message(self) -> None:
        err = WriteError(kind="disk_full", message="")
        assert "disk" in write_error_message(err).lower()

    def test_unexpected_includes_detail(self) -> None:
        err = WriteError(kind="unexpected", message="something went wrong")
        assert "something went wrong" in write_error_message(err)
