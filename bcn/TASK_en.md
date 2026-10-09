# Task: Excel preprocessing skeleton

## Goal

Build a minimal Python repository for preprocessing Excel data.

At this stage, build only the skeleton: a file goes in, a file comes out. The preprocessing logic is not defined yet. It will be added later, once the input files are better understood.

## Structure

The repository contains one or two Python files:

| File | Role |
|------|------|
| `main.py` | Command-line entry point. Parses arguments and calls the processing functions. Contains no processing logic. |
| Second module (any name) | Contains all functions that operate on the file. |

## Command-line interface

`main.py` is run from the command line and accepts:

- **Input path** (required): path to the source Excel file.
- **Output path** (required): path where the processed file is written.
- **Optional configuration** (optional): additional parameters. None are defined yet; the interface should allow adding them later.

## Initial behavior (placeholder)

1. Read the file from the input path.
2. Pass it through a placeholder operation that does nothing (returns the data unchanged).
3. Write the result to the output path.

The result is effectively a copy of the input file from location A to location B.

## Out of scope

- Real preprocessing logic. It will be designed and added later.
