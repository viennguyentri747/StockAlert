Stock Alert (CLI MVP)
=====================

Quick, local CLI for managing watchlists and simple alerts, and running an evaluation loop with a fake data provider (no network needed). By default, data is stored in `./.stockalert` (set `STOCKALERT_HOME` to override, e.g., `~/.stockalert`).

Install/Run
-----------

- Requires Python 3.9+
- Run via module:

  - `python -m stock_alert --help`

Example Usage
-------------

- Add symbols to watchlist:
  - `python -m stock_alert watchlist add AAPL MSFT TSLA`
- List watchlist:
  - `python -m stock_alert watchlist list`
- Create an alert:
  - `python -m stock_alert alert create --symbol AAPL --when "price >= 200" --name aapl-200`
  - `python -m stock_alert alert create --symbol TSLA --when "pct_day <= -3" --name tsla-drop`
- List alerts:
  - `python -m stock_alert alerts`
- Run the loop (2 iterations, 5s interval, verbose):
  - `python -m stock_alert run --interval 5s --verbose --provider finnhub`
  - Use real data (Yahoo, no key): `python -m stock_alert run --provider yahoo`
  - Alpha Vantage (requires key): `ALPHAVANTAGE_API_KEY=... python -m stock_alert run --provider alphavantage`
  - Finnhub (requires key): `FINNHUB_API_KEY=... python -m stock_alert run --provider finnhub`

Notes
-----

- This MVP uses a fake data provider with deterministic-ish prices and random day % changes.
- Real providers available: Yahoo Finance (no key), Alpha Vantage, Finnhub (both require API keys; free tiers exist and are rate limited).
- Files created under `~/.stockalert/`: `watchlist.json`, `alerts.json`, `config.json`.
- Conditions supported: `price >=|<= VALUE`, `pct_day >=|<= VALUE`.
# StockAlert
