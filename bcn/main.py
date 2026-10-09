"""Command-line entry point: parses arguments and runs the preprocessing."""

import argparse
from pathlib import Path

from preprocessing import process


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preprocess an Excel file.")
    parser.add_argument("input", type=Path, help="path to the source Excel file")
    parser.add_argument(
        "output", type=Path, help="path where the processed file is written"
    )
    # Optional configuration arguments go here once they are defined.
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"input file not found: {args.input}")
    if args.input.resolve() == args.output.resolve():
        parser.error("output path must differ from input path")

    process(args.input, args.output)


if __name__ == "__main__":
    main()
