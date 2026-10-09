# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

A collection of small, unrelated scripts that don't need their own repository. Each task lives in its own top-level directory and is self-contained: it has its own `pyproject.toml`, `.python-version`, and dependencies. Nothing is shared between task directories, and there is no root-level Python project.

Each task is usually a single code file, most often a Python script.

## Task directories

Each task directory may contain:

- `TASK.md`: the original task description, written in Polish.
- `TASK_en.md`: the English version. Treat it as the spec for the task.
- `main.py`: the entry point.

Read `TASK_en.md` before changing a task's code.

### `bcn/`

An Excel preprocessing tool. Per `bcn/TASK_en.md`, it should stay at one or two Python files:

- `main.py` is only a CLI proxy. It parses the input path, the output path and future optional config, then calls the processing functions. It holds no processing logic.
- A second module holds all the file-manipulation functions.

The current target is a placeholder pipeline: read the Excel file, pass it through a no-op transform, and write it to the output path. Real preprocessing logic is explicitly out of scope until the input files are understood. The CLI should leave room for more options later.

The skeleton is in place. `main.py` uses argparse, and the second module is `preprocessing.py`, which runs `read_workbook` → `transform` → `write_workbook`. Real logic goes into `transform()`, which takes and returns a dict mapping sheet name to DataFrame and currently returns it unchanged. Sheets are read with `header=None` so that every row is data and the file round-trips unchanged. Revisit this once the header layout of the real files is known.

Usage: `uv run main.py <input.xlsx> <output.xlsx>`

## Commands

Projects are managed with `uv` and require Python 3.13. Run these commands from inside the task directory, for example `bcn/`:

```sh
uv run main.py <args>     # run the script (creates .venv and syncs deps on first run)
uv add <package>          # add a dependency to that task's pyproject.toml
```

No test suite, linter or formatter is configured yet.
