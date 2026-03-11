from __future__ import annotations

from dataclasses import dataclass, field


def _str_list() -> list[str]:
    return []


@dataclass(frozen=True)
class Ok[T]:
    value: T
    warnings: list[str] = field(default_factory=_str_list)


@dataclass(frozen=True)
class Err[E]:
    error: E


type Result[T, E] = Ok[T] | Err[E]
