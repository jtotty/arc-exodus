from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

type WriteErrorKind = Literal["permission_denied", "disk_full", "unexpected"]


@dataclass(frozen=True)
class WriteError:
    kind: WriteErrorKind
    message: str
