"""Transform Arc bookmark data into Chrome bookmark format.

All functions in this module are pure:
- No file I/O
- No side effects
- Deterministic output for a given input

This makes them trivially testable and composable.
"""

from __future__ import annotations
