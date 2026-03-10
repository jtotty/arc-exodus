"""Data models for Arc and Chrome bookmark schemas.

Arc uses a flat list of items with parent-child ID references.
Chrome uses a nested tree structure.

See thoughts/james/initial-research.md for full schema documentation.
"""

from __future__ import annotations
