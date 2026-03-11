"""CLI entry point for arc-exodus."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from arc_exodus.arc import default_sidebar_path, get_space_items, read_sidebar
from arc_exodus.arc.messages import read_error_message
from arc_exodus.chrome import (
    default_chrome_base_dir,
    list_chrome_profiles,
    write_bookmarks,
)
from arc_exodus.chrome.messages import write_error_message
from arc_exodus.result import Err
from arc_exodus.transformer import transform_space

if TYPE_CHECKING:
    from arc_exodus.arc import ArcSidebar


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


def _resolve_space_name(args: argparse.Namespace, sidebar: ArcSidebar) -> str:
    if args.space is not None:
        return str(args.space)
    titles = [s.title for s in sidebar.spaces]
    return titles[_prompt_choice("Select Arc space to export", titles)]


def _resolve_profile_path(args: argparse.Namespace) -> Path:
    if args.profile is not None:
        return Path(args.profile)
    profiles = list_chrome_profiles(default_chrome_base_dir())
    names = [name for name, _ in profiles]
    return profiles[_prompt_choice("Select Chrome profile", names)][1]


def main() -> None:
    """Entry point for the arc-exodus CLI."""
    try:
        _run()
    except KeyboardInterrupt:
        print("\nAborted.")


def _run() -> None:
    args = create_parser().parse_args()

    sidebar_result = read_sidebar(default_sidebar_path())
    if isinstance(sidebar_result, Err):
        print(read_error_message(sidebar_result.error))
        return
    sidebar = sidebar_result.value
    for w in sidebar_result.warnings:
        print(f"Warning: {w}")

    space_name = _resolve_space_name(args, sidebar)
    profile_path = _resolve_profile_path(args)

    space_result = get_space_items(sidebar, space_name)
    if isinstance(space_result, Err):
        print(read_error_message(space_result.error))
        return

    transform_result = transform_space(space_result.value)
    for w in transform_result.warnings:
        print(f"Warning: {w}")
    write_result = write_bookmarks(transform_result.value, profile_path)
    if isinstance(write_result, Err):
        print(write_error_message(write_result.error))
        return
    print("Done.")


if __name__ == "__main__":
    main()
