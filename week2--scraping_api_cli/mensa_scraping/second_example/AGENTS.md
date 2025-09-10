# Repository Guidelines

## Project Structure & Modules
- `scrape.py`: Crawlee + Typer CLI that saves daily HTML to `data/{city}/{university|city}/{mensa}/{YYYY-MM-DD}.html`.
- `parse.py`: Parses HTML in `data/` into SQLite (`mensa_data.db`).
- `extract_menu_unix.py`: Unix-friendly JSONL extractor using `pup`; works with `data_wget/` trees.
- `data/`, `data_wget/`: Downloaded site mirrors; keep committed only if intentionally sharing fixtures.
- `storage/`: Runtime scratch/state (created by tools); avoid committing large artifacts.
- `final_test.db`, `mensa_data.db`: Example SQLite databases; prefer generating locally.
- `README.md`: Full usage and wget strategies; read first.

## Build, Test, Run
- Install tooling: `uv` (Python 3.12+), and for Option 2/3 `wget`/`wget2`; for Unix extractor: `pup`, `rg`, `jq`.
- Scrape (limited): `uv run scrape.py --limit 10` (use `--overwrite` to refresh today’s files).
- Parse to DB: `uv run parse.py --db-path mensa_data.db`.
- wget mirror (example): see `README.md` or run the provided command into `data_wget/`.
- Unix pipeline (example): `rg -l "aw-weekly-menu" data_wget | uv run extract_menu_unix.py | jq -s '.'`.

## Coding Style & Naming
- Python, PEP 8, 4-space indent; use type hints, `pathlib.Path`, and f-strings.
- Functions/methods in snake_case; CLIs via Typer with explicit option names (e.g., `--db-path`).
- Logging via `rich` + `RichHandler`; avoid bare prints in library code.
- Keep I/O paths relative to repo root (`data/`, `storage/`).

## Testing Guidelines
- No test suite yet. Add `tests/` with `pytest` (e.g., fixtures of small HTML pages under `tests/fixtures/`).
- Quick sanity checks:
  - Parse count: `uv run parse.py --db-path test.db && sqlite3 test.db 'select count(*) from menu_items;'`.
  - HTML presence: `find data -name '*.html' | wc -l`.
- Prefer deterministic sample data committed under `tests/fixtures/` rather than large crawls.

## Commit & PR Guidelines
- Use clear, imperative messages scoped by area: `scrape: …`, `parse: …`, `docs: …`.
- PRs: include a summary, linked issue, sample command(s) run, and before/after notes (e.g., row counts, file paths).
- Keep changes small and focused; update `README.md` when flags/paths change.

## Security & Operations
- Be respectful with scraping: rate limit; prefer wget depth controls; avoid committing bulk mirrors.
- SQLite files may contain local paths; don’t share sensitive paths in PR screenshots or logs.
