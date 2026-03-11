from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

type ReadErrorKind = Literal[
    "file_not_found",
    "permission_denied",
    "malformed_json",
    "invalid_structure",
    "space_not_found",
]


@dataclass(frozen=True)
class ReadError:
    kind: ReadErrorKind
    message: str
