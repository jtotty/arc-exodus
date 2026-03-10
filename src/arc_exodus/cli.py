import argparse


def create_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="arc-exodus",
        description="Transfer bookmarks from Arc browser to Chrome",
    )
    return parser


def main() -> None:
    """Entry point for the arc-exodus CLI."""
    parser = create_parser()
    parser.parse_args()
    parser.print_help()


if __name__ == "__main__":
    main()
