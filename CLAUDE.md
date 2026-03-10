# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

arc-exodus is a Python CLI tool that transfers bookmarks from a single Arc browser profile (space) to a chosen Chrome profile. It reads Arc's `StorableSidebar.json`, transforms the data, and writes Chrome's `Bookmarks` JSON format.

## Commands

```bash
uv run pytest                    # run all tests
uv run pytest tests/test_cli.py  # run a single test file
uv run pytest -k "test_name"     # run tests matching a pattern
uv run ruff check .              # lint
uv run ruff format .             # format (drop --check to auto-fix)
uv run pyright                   # type check (strict mode)
uv run arc-exodus                # run the CLI
```

## Architecture

Pipeline design with strict module boundaries:

```
arc_reader → transformer → chrome_writer
                ↑
              models (shared data contracts)
                ↑
               cli (orchestrates the pipeline)
```

- **models.py** — Data classes for both Arc and Chrome schemas. No dependencies on other modules.
- **arc_reader.py** — Reads Arc's `StorableSidebar.json` from disk. Depends only on `models`.
- **transformer.py** — Pure functions converting Arc models to Chrome models. No I/O, no side effects. Depends only on `models`.
- **chrome_writer.py** — Writes Chrome `Bookmarks` JSON to disk. Depends only on `models`.
- **cli.py** — Argument parsing and pipeline orchestration. Depends on all above.

Modules are orthogonal: `arc_reader` knows nothing about Chrome, `chrome_writer` knows nothing about Arc, `transformer` knows nothing about files.

## Conventions

- `from __future__ import annotations` in every source file
- Pyright strict mode — all functions need type annotations, no implicit `Any`
- `ANN` rules relaxed in tests (no annotation requirements for test functions/fixtures)
- Tests use class-based grouping (e.g., `TestCreateParser`)
- `src/` layout with `uv` as the package manager
