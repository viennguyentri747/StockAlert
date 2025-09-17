Stock Alert (CLI)
=====================

A command-line tool for managing stock watchlists and price alerts. By default, data is stored in `./.stockalert` (set `STOCKALERT_HOME` to override, e.g., `~/.config/stockalert`).

Install
-------

- Requires Python 3.9+
- Clone the repository and install in editable mode:
  \`\`\`bash
  pip install -e .
  \`\`\`

Example Usage
-------------

The tool is split into a main launcher (`stock-alert`) and sub-tools (`manage`, `monitor`).

### Manage Watchlist and Alerts (`stock-alert manage`)

- Add symbols to watchlist: `stock-alert manage watchlist add AAPL MSFT TSLA`
- List watchlist: `stock-alert manage watchlist list`
- Create an alert: `stock-alert manage alert create --symbol AAPL --when "price >= 200"`
- List alerts: `stock-alert manage alerts`

### Monitor Stocks (`stock-alert monitor`)

- Run the monitoring loop: `stock-alert monitor --interval 5s --verbose`
- Use real data providers (some require API keys set in `.my_credential.env`):
  - Finnhub: `stock-alert monitor --provider finnhub`
  - Yahoo (no key): `stock-alert monitor --provider yahoo`
  - Alpha Vantage: `stock-alert monitor --provider alphavantage`

Notes
-----

- This MVP uses a fake data provider with deterministic-ish prices and random day % changes.
- Real providers available: Yahoo Finance (no key), Alpha Vantage, Finnhub (both require API keys; free tiers exist and are rate limited).
- Files created under `$STOCKALERT_HOME/`: `watchlist.json`, `alerts.json`.
- Conditions supported: `price >=|<= VALUE`, `pct_day >=|<= VALUE`, `volume >=|<= VALUE`.
