"""CLI entry point for arc-exodus."""

from __future__ import annotations

import argparse
from pathlib import Path

from arc_exodus.arc import default_sidebar_path, get_space_items, read_sidebar
from arc_exodus.chrome import (
    default_chrome_base_dir,
    list_chrome_profiles,
    write_bookmarks,
)
from arc_exodus.transformer import transform_space


def create_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="arc-exodus",
        description="Transfer bookmarks from Arc browser to Chrome",
    )
    parser.add_argument(
        "--space",
        default=None,
        metavar="NAME",
        help="Name of the Arc space to export (e.g. 'Personal')",
    )
    parser.add_argument(
        "--profile",
        default=None,
        metavar="PATH",
        type=Path,
        help="Path to the Chrome profile directory",
    )
    return parser


def _prompt_choice(prompt: str, options: list[str]) -> int:
    """Display a numbered list and return the 0-based index of the user's choice."""
    print(f"\n{prompt}:")
    for i, option in enumerate(options, start=1):
        print(f"  {i}. {option}")
    while True:
        raw = input(f"Enter number [1-{len(options)}]: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1


def main() -> None:
    """Entry point for the arc-exodus CLI."""
    try:
        _run()
    except KeyboardInterrupt:
        print("\nAborted.")


def _run() -> None:
    args = create_parser().parse_args()

    sidebar = read_sidebar(default_sidebar_path())

    if args.space is not None:
        space_name: str = args.space
    else:
        titles = [s.title for s in sidebar.spaces]
        space_name = titles[_prompt_choice("Select Arc space to export", titles)]

    if args.profile is not None:
        profile_path: Path = args.profile
    else:
        profiles = list_chrome_profiles(default_chrome_base_dir())
        names = [name for name, _ in profiles]
        profile_path = profiles[_prompt_choice("Select Chrome profile", names)][1]

    write_bookmarks(transform_space(get_space_items(sidebar, space_name)), profile_path)
    print("Done.")


if __name__ == "__main__":
    main()
