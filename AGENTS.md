# Repository Guidelines

## Project Structure & Module Organization
- Source lives in `stock_alert/`:
  - `core/` (models, parsing), `engine/` (loop/timing), `data_providers/` (quote sources),
    `store/` (JSON persistence), `cli.py` (argparse CLI), `__main__.py` (entrypoint).
- Runtime data in `./.stockalert` (override with `STOCKALERT_HOME`). Key files: `watchlist.json`,
  `alerts.json`, `config.json`.
- Tests under `tests/` mirror package paths (e.g., `tests/engine/test_runner.py`).

## Build, Test, and Development Commands
- Python 3.9+; MVP has no external dependencies.
- Help: `python -m stock_alert --help`.
- Watchlist: `python -m stock_alert watchlist add AAPL TSLA`.
- Create alert: `python -m stock_alert alert create --symbol AAPL --when "price >= 200" --name aapl-200`.
- Run loop: `python -m stock_alert run --interval 5s --iterations 2 --verbose`.
- Tests: `pytest -q` (place tests under `tests/`).

## Coding Style & Naming Conventions
- Follow PEP 8, 4-space indentation, max line length 100.
- Use type hints and `@dataclass` where appropriate (see `core/models.py`).
- Naming: modules/functions `snake_case`, classes `CamelCase`, constants `UPPER_SNAKE_CASE`.
- Keep CLI changes additive; register new subcommands in `stock_alert/cli.py`.

## Testing Guidelines
- Framework: `pytest`.
- Test naming: files `test_*.py`; functions `test_*`.
- Aim for coverage on parsing, cooldown logic, and interval parsing.
- Run fast, isolated tests; avoid network or external I/O.

## Commit & Pull Request Guidelines
- Commits: imperative present, concise subject (≤ 72 chars).
  Example: `feat(cli): add alerts list subcommand`.
- PRs: include a short description, usage examples, and any data/config migration notes.
  Link issues and attach CLI output/screenshots when relevant.

## Security & Configuration Tips
- Do not commit real API keys. New providers read secrets from env vars and implement
  `DataProvider` under `data_providers/`.
- Keep all writes within `STOCKALERT_HOME`. Use JSON helpers in `store/files.py` for atomic saves.

## Architecture Overview
- Event loop in `engine/runner.py`; calls provider `get_quote()` and alert `should_trigger()`.
- I/O hooks: `on_tick` and `on_alert`.
- To add a provider, subclass `DataProvider` and wire it via the CLI.

