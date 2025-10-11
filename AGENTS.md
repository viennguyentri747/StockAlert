# Repository Guidelines

## Project Structure & Module Organization
Source code lives in `stock_alert/`. Keep domain models and parsing helpers inside `core/`, execution timing in `engine/`, data provider integrations under `data_providers/`, and JSON persistence helpers in `store/`. The CLI entry points are `cli.py` and `__main__.py`. Runtime state is stored in `./.stockalert` (override via `STOCKALERT_HOME`) with `watchlist.json`, `alerts.json`, and `config.json`. Mirror new tests inside `tests/` using the same package layout, e.g. `tests/engine/test_runner.py`.

## Build, Test, and Development Commands
Use Python 3.9+. Inspect available commands with `python -m stock_alert --help`. Add tickers using `python -m stock_alert watchlist add AAPL TSLA`, create alerts through `python -m stock_alert alert create --symbol AAPL --when "price >= 200" --name aapl-200`, and exercise the loop via `python -m stock_alert run --interval 5s --iterations 2 --verbose`. Run the fast test suite with `pytest -q` from the repo root.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation and max line length 100. Favour type hints and `@dataclass` for immutable models (see `core/models.py`). Name modules and functions in `snake_case`, classes in `CamelCase`, and constants in `UPPER_SNAKE_CASE`. Keep CLI extensions additive by registering new subcommands in `stock_alert/cli.py` without breaking existing flags.

## Testing Guidelines
Author tests with `pytest`. Name files `tests/<pkg>/test_*.py` and functions `test_*`. Focus coverage on parser behaviour, interval parsing, cooldown handling, and alert trigger logic. Tests must be deterministic and avoid external network or file system writes outside `STOCKALERT_HOME`.

## Commit & Pull Request Guidelines
Write commit subjects in imperative present, ≤72 characters (e.g. `feat(cli): add alerts list subcommand`). Link related issues in the body. Pull requests should summarise behaviour changes, include CLI examples when useful, and describe any data or config migrations needed. Attach screenshots or captured CLI output if it clarifies user-facing updates.

## Security & Configuration Tips
Never commit real API keys. Inject provider credentials via environment variables and confine persistence to `STOCKALERT_HOME` by using helpers in `store/files.py` for atomic writes. Document new configuration knobs in `config.json` and surface defaults through the CLI help text.

## Architecture Overview
The event loop in `engine/runner.py` orchestrates ticks, fetching quotes through each `DataProvider.get_quote()` and evaluating alerts via `Alert.should_trigger()`. Hooks `on_tick` and `on_alert` handle I/O side effects. When adding a provider, subclass `DataProvider`, keep network access encapsulated, and expose it through CLI wiring so it can be selected without code changes.
