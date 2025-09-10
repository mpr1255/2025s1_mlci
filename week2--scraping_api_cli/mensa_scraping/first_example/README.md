Mensa Menu CLI (Typer)

This simple CLI fetches the daily Mensa menu and prints it as CSV (default) or JSON. It’s designed for teaching basic CLI usage, piping, and working with `sqlite-utils`.

Requirements
- `uv` to run the script with inline dependencies
- `sqlite-utils` for the database examples

Show Help
- `uv run test.py` (no args) — shows help
- `uv run test.py --help`

Basic Usage
- CSV (default): `uv run test.py 2025-08-25`
- Explicit CSV: `uv run test.py 2025-08-25 --csv`
- JSON: `uv run test.py 2025-08-25 --json`

Pipe to sqlite-utils
- CSV input (specify `--csv` for sqlite-utils):
  - `uv run test.py 2025-08-25 --csv | sqlite-utils insert menu.db menu - --csv --pk date`

- JSON input (default JSON array is accepted by sqlite-utils):
  - `uv run test.py 2025-08-25 --json | sqlite-utils insert menu.db menu - --pk date`

Alternate Primary Keys
- Use category as PK: `--pk category`
- Composite keys (category + date): `--pk category --pk date`

Inspect the database
- List tables: `sqlite-utils tables menu.db`
- Preview rows: `sqlite-utils rows menu.db menu --limit 5`

Notes
- If there is no menu for the requested date, the CLI exits without output (useful for pipelines).
- The CSV headers are: `date,category,description,price`.

