from __future__ import annotations

from arc_exodus.result import Err, Ok


class TestOk:
    def test_holds_value(self) -> None:
        expected = 42
        result = Ok(value=expected)
        assert result.value == expected

    def test_warnings_default_to_empty(self) -> None:
        result = Ok(value="hello")
        assert result.warnings == []

    def test_accepts_warnings(self) -> None:
        result = Ok(value="hello", warnings=["something was skipped"])
        assert result.warnings == ["something was skipped"]

    def test_isinstance_check(self) -> None:
        assert isinstance(Ok(value=1), Ok)
        assert not isinstance(Ok(value=1), Err)


class TestErr:
    def test_holds_error(self) -> None:
        result = Err(error="oops")
        assert result.error == "oops"

    def test_isinstance_check(self) -> None:
        assert isinstance(Err(error="x"), Err)
        assert not isinstance(Err(error="x"), Ok)
