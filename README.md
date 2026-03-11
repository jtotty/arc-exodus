# arc-exodus

Transfer bookmarks from an [Arc](https://arc.net) browser space to a Chrome profile.

arc-exodus reads Arc's `StorableSidebar.json`, picks a single space, and appends an "Imported from Arc" folder to Chrome's `Bookmarks` file. Existing Chrome bookmarks are preserved. The original `Bookmarks` file is backed up before every write.

## Requirements

- macOS
- [Arc](https://arc.net) installed and launched at least once
- [uv](https://docs.astral.sh/uv/) (`brew install uv`)

## Installation

```bash
git clone https://github.com/jtotty/arc-exodus.git
cd arc-exodus
uv sync
```

## Usage

### Interactive

```bash
uv run arc-exodus
```

Prompts you to choose an Arc space and a Chrome profile.

### Non-interactive

```bash
uv run arc-exodus --space Personal --profile "/Users/you/Library/Application Support/Google/Chrome/Default"
```

| Flag | Description |
|---|---|
| `--space NAME` | Arc space to export (e.g. `Personal`, `Work`) |
| `--profile PATH` | Path to the Chrome profile directory |

### What it does

1. Reads `~/Library/Application Support/Arc/StorableSidebar.json`
2. Transforms the chosen space's tabs and folders into Chrome bookmark nodes
3. If a `Bookmarks` file already exists in the target profile, merges by appending — existing bookmarks are untouched
4. Backs up the existing `Bookmarks` file to `Bookmarks.bak.<timestamp>`
5. Writes the new file atomically (temp file + rename)

## Development

```bash
uv run pytest          # tests
uv run pyright         # type checking (strict)
uv run ruff check .    # lint
uv run ruff format .   # format
```
