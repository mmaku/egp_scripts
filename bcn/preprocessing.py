"""Functions that read, transform and write the Excel data."""

from pathlib import Path

import pandas as pd

# Sheet name -> sheet contents, in workbook order.
Sheets = dict[str, pd.DataFrame]


def read_workbook(path: Path) -> Sheets:
    # header=None keeps every row as data, so the file round-trips as-is
    # until the real layout of the input files is known.
    return pd.read_excel(path, sheet_name=None, header=None)


def transform(sheets: Sheets) -> Sheets:
    """Placeholder for the preprocessing logic: returns the data unchanged."""
    return sheets


def write_workbook(sheets: Sheets, path: Path) -> None:
    with pd.ExcelWriter(path) as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, header=False, index=False)


def process(input_path: Path, output_path: Path) -> None:
    write_workbook(transform(read_workbook(input_path)), output_path)
