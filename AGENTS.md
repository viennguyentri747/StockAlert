# Repository Guidelines

## Project Structure & Module Organization
- Source lives in `stock_alert/`:
  - `core/` (models, parsing), `engine/` (loop/timing), `data_providers/` (quote sources),
    `store/` (JSON persistence), `cli.py` (argparse CLI), `__main__.py` (entrypoint).
- Runtime data in `./.stockalert` (override with `STOCKALERT_HOME`). Key files: `watchlist.json`, `alerts.json`, `config.json`.
- Tests under `tests/` mirroring package paths (e.g., `tests/engine/test_runner.py`).

## Build, Test, and Development Commands
- Run CLI help: `python -m stock_alert --help`
- Add symbols: `python -m stock_alert watchlist add AAPL TSLA`
- Create alert: `python -m stock_alert alert create --symbol AAPL --when "price >= 200" --name aapl-200`
- Run loop: `python -m stock_alert run --interval 5s --iterations 2 --verbose`
- Python 3.9+; MVP has no external dependencies.

## Coding Style & Naming Conventions
- Follow PEP 8; 4‑space indentation; lines ≤ 100 chars.
- Use type hints and `@dataclass` where appropriate (see `core/models.py`).
- Naming: modules/functions `snake_case`, classes `CamelCase`, constants `UPPER_SNAKE_CASE`.
- Keep CLI changes additive; register subcommands in `stock_alert/cli.py`.

## Testing Guidelines
- Framework: `pytest`. Run: `pytest -q`.
- Place tests under `tests/` with `test_*.py` and `test_*` functions.
- Aim for coverage on parsing, cooldown logic, and interval parsing.

## Commit & Pull Request Guidelines
- Commits: imperative present, concise subject (≤ 72 chars). Example: `feat(cli): add alerts list subcommand`.
- PRs: include a short description, usage examples, and any data/config migration notes. Link issues and add CLI output/screenshots when relevant.

## Security & Configuration Tips
- Do not commit real API keys. New providers should read secrets from env vars and implement `DataProvider` in `data_providers/`.
- Keep all writes within `STOCKALERT_HOME`. Use JSON helpers in `store/files.py` for atomic saves.

## Architecture Notes
- Event loop: `engine/runner.py`; calls provider `get_quote()` and alert `should_trigger()`.
- I/O hooks: `on_tick` and `on_alert`.
- To add a provider, subclass `DataProvider` and wire it via the CLI.

