# Repository Guidelines

## Project Structure & Module Organization
- Source lives in `stock_alert/` with submodules:
  - `core/` (models, parsing), `engine/` (loop + timing), `data_providers/` (quote sources), `store/` (JSON persistence), `cli.py` (argparse commands), `__main__.py` (entrypoint).
- Runtime data is stored in `./.stockalert` by default; override with `STOCKALERT_HOME`.
- Key data files: `watchlist.json`, `alerts.json`, `config.json`.

## Build, Test, and Development Commands
- Run CLI: `python -m stock_alert --help`
- Typical flows:
  - Add symbols: `python -m stock_alert watchlist add AAPL TSLA`
  - Create alert: `python -m stock_alert alert create --symbol AAPL --when "price >= 200" --name aapl-200`
  - Run loop: `python -m stock_alert run --interval 5s --iterations 2 --verbose`
- Python version: 3.9+; no external deps in MVP.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4‑space indentation; keep lines ≤ 100 chars.
- Use type hints and dataclasses where appropriate (see `core/models.py`).
- Naming: modules and functions `snake_case`, classes `CamelCase`, constants `UPPER_SNAKE_CASE`.
- Keep CLIs additive and explicit; subcommands live in `cli.py` and register via `argparse`.

## Testing Guidelines
- Use `pytest` (recommended). Place tests under `tests/` mirroring package paths, e.g. `tests/engine/test_runner.py`.
- Test names: files `test_*.py`, functions `test_*` with clear Arrange‑Act‑Assert.
- Aim for coverage on parsing, cooldown logic, and interval parsing. Run: `pytest -q`.

## Commit & Pull Request Guidelines
- Commits: imperative present, concise subject (≤ 72 chars), optional body for context.
  - Example: `feat(cli): add alerts list subcommand`
- PRs: include a short description, reproduction/usage examples, and any config or data migration notes. Link issues when applicable.
- Add screenshots or sample output for CLI changes.

## Security & Configuration Tips
- Never commit real API keys. For new providers, read secrets from env vars and implement `DataProvider` in `data_providers/`.
- Keep writes within `STOCKALERT_HOME`. Use the JSON helpers in `store/files.py` for atomic saves.

## Architecture Notes
- Event loop is in `engine/runner.py` and calls provider `get_quote()` and alert `should_trigger()`; callbacks `on_tick` and `on_alert` handle I/O.
- To add a real provider, subclass `DataProvider` and register it in the CLI wiring.
