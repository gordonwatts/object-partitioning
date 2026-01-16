# Repository Guidelines

## Project Structure & Module Organization

- `src/atlas_object_partitioning/` holds the library code and CLI entrypoint (`partition.py`).
- `tests/atlas_object_partitioning/` contains pytest-based unit tests (e.g., `test_histograms.py`).
- Top-level metadata lives in `pyproject.toml`, with packaging and tool configuration.

## Build, Test, and Development Commands

- `python -m pip install -e .` installs the package in editable mode.
- `python -m pip install -e ".[test]"` installs test and lint tools.
- `atlas-object-partitioning --help` shows CLI options and validates entrypoint wiring.
- `pytest` runs the test suite.
- `black src tests` formats code; `flake8 src tests` checks linting rules.

## Coding Style & Naming Conventions

- Python 3.10+ is required; use 4-space indentation and type hints where helpful.
- Follow Black formatting defaults and keep imports tidy.
- Use descriptive, domain-specific names (e.g., `partition_objects`, `scan_dataset`).
- Keep CLI options and output file names consistent with existing patterns
  (e.g., `bin_boundaries.yaml`, parquet outputs).

## Testing Guidelines

- Tests are written with pytest; name files `test_*.py` under `tests/atlas_object_partitioning/`.
- Prefer small, deterministic tests around histogram/bin logic and dataset scanning.
- Run the full suite with `pytest` before opening a PR.

## Commit & Pull Request Guidelines

- Recent commits use short, imperative summaries (e.g., “Add ability to ignore some of the data axes”).
- If a change is tied to an issue or PR, include the reference in the message when available.
- PRs should include: a clear description, the motivation/impact, and any sample output
  (CLI snippets or small tables) when behavior changes.

## Configuration & Data Access Notes

- ServiceX access requires a valid `servicex.yaml` token; avoid committing credentials.
- Large dataset runs can be expensive; document any performance-impacting changes.
