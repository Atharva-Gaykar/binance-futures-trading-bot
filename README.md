# 📈 Binance Futures Testnet Trading Bot

A CLI-based Python trading bot for placing orders on **Binance Futures Testnet (USDT-M)**, with an optional Streamlit web dashboard. Built for the Python Developer Intern application task — Primetrade.ai.

**Repository:** https://github.com/Atharva-Gaykar/binance-futures-trading-bot

---

## ✨ Features

- Place **MARKET** and **LIMIT** orders on Binance Futures Testnet (USDT-M)
- Support for both **BUY** and **SELL** sides
- **Bonus #1:** **STOP_LIMIT** conditional orders, routed through Binance's Algo Order API
- **Bonus #2:** Interactive **Streamlit web dashboard** with a Binance-inspired dark/yellow theme
- CLI input validation via **Typer** + **Pydantic**
- Clean, layered architecture — client / orders / validators / logging / CLI kept separate
- Full request/response/error logging to file
- Robust exception handling for invalid input, API errors, and network failures
- Automatic correction for local clock drift against Binance server time

---

## 🗂️ Project Structure

```
binance-futures-trading-bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance client wrapper — auth, raw order placement
│   ├── orders.py           # Order placement logic, request/response formatting
│   ├── validators.py       # Pydantic models for CLI input validation
│   └── logging_config.py   # Logging setup (file + console handlers)
├── cli.py                  # Typer CLI entry point
├── app.py                  # Streamlit web dashboard (bonus)
├── logs/
│   ├── market_order_sample.log
│   ├── limit_order_sample.log
│   └── stop_limit_order_sample.log   # bonus order type sample
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🧩 Basic System Design

[View on Eraser![](https://app.eraser.io/workspace/Meagp4s4Nn7rJIL0TqzP/preview?diagram=hb3l4IRO8k40bIAVdSvM&type=embed)](https://app.eraser.io/workspace/Meagp4s4Nn7rJIL0TqzP?diagram=hb3l4IRO8k40bIAVdSvM)


---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/Atharva-Gaykar/binance-futures-trading-bot
cd binance-futures-trading-bot
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Binance Futures Testnet API credentials

1. Register and activate an account at the [Binance Futures Testnet](https://testnet.binancefuture.com).
2. Generate an API key and secret from the testnet dashboard.
3. Copy `.env.example` to `.env` and fill in your real credentials:

```bash
# macOS/Linux
cp .env.example .env

# Windows
copy .env.example .env
```

`.env` should look like:

```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
BINANCE_TESTNET_BASE_URL=https://testnet.binancefuture.com/fapi
```

> ⚠️ `.env` is gitignored and must never be committed. Only `.env.example` (placeholder values) is tracked in git.

---

## ▶️ How to Run — CLI

The bot exposes a single `place-order` command.

### Place a MARKET order

```bash
python cli.py place-order --symbol BTCUSDT --side BUY --order-type MARKET --quantity 0.01
```

### Place a LIMIT order

```bash
python cli.py place-order --symbol BTCUSDT --side SELL --order-type LIMIT --quantity 0.005 --price 68500
```

### Place a STOP_LIMIT order (bonus)

```bash
python cli.py place-order --symbol BTCUSDT --side BUY --order-type STOP_LIMIT --quantity 0.01 --price 70300 --stop-price 70200
```

Run `python cli.py place-order --help` for the full option list.

### CLI Options

| Option | Required | Description |
|---|---|---|
| `--symbol` | Yes | Trading pair, e.g. `BTCUSDT`. Must be a USDT-M pair. |
| `--side` | Yes | `BUY` or `SELL` |
| `--order-type` | Yes | `MARKET`, `LIMIT`, or `STOP_LIMIT` |
| `--quantity` | Yes | Order quantity (must be > 0) |
| `--price` | Required for LIMIT / STOP_LIMIT | Limit execution price |
| `--stop-price` | Required for STOP_LIMIT | Trigger price for the conditional order |

---

## 🖥️ How to Run — Web Dashboard (Bonus)

A Streamlit dashboard is available as an alternative to the CLI, styled with a Binance-inspired dark/yellow theme.

```bash
streamlit run app.py
```

This opens a browser UI where you can configure and place orders interactively — symbol, side, order type, quantity, price, and stop price are set via sidebar controls, with live order preview and clean success/error feedback.

---

## 📤 Output

Every order placed (CLI or UI) prints:

1. **Request summary** — symbol, side, type, quantity, price/stop-price if applicable
2. **Response summary** — order/algo ID, status, executed quantity, average price (if available)
3. **Success/failure message**

All requests, responses, and errors are also logged to `logs/trading_bot.log`.

---

## 📄 Sample Logs

Log excerpts from successful test runs are included in the `logs/` folder:

| File | Order Type |
|---|---|
| `logs/market_order_sample.log` | MARKET (required) |
| `logs/limit_order_sample.log` | LIMIT (required) |
| `logs/stop_limit_order_sample.log` | STOP_LIMIT (bonus) |


---

## 🧠 Design Notes

- **MARKET / LIMIT** orders are placed via Binance's standard Futures order endpoint (`futures_create_order`), returning `orderId` and `status`.
- **STOP_LIMIT** orders are conditional orders. Per Binance's mandatory migration (effective 2025-12-09), conditional order types (`STOP`, `STOP_MARKET`, `TAKE_PROFIT`, `TAKE_PROFIT_MARKET`) must be placed via the dedicated **Algo Order API** (`futures_create_algo_order`) rather than the standard order endpoint. The bot automatically routes `STOP_LIMIT` requests here. Algo responses use `algoId` / `algoStatus` instead of `orderId` / `status`; the response formatter handles both shapes transparently.
- For MARKET orders, the bot performs a brief follow-up status query (`get_order_status`) to confirm the true fill status and executed quantity, since the initial acknowledgment may not yet reflect the final fill.
- The client corrects for local system clock drift against Binance server time on startup (`timestamp_offset`), avoiding `-1021 Timestamp` errors.

---

## 📝 Assumptions

- Only **USDT-M Futures** pairs are supported (symbols ending in `USDT`); Coin-M Futures is out of scope.
- `timeInForce` defaults to `GTC` (Good-Til-Cancelled) for LIMIT and STOP_LIMIT orders.
- Each CLI invocation places a single order — no persistent session or multi-order batching in this version.
- Testnet order fills are not guaranteed instantly (especially for LIMIT/STOP_LIMIT orders resting on the book); sample logs reflect successful order **acceptance** (`status: NEW` / `algoStatus: NEW`), which confirms the order was correctly placed on Binance's side.

---

## 📦 Requirements

See `requirements.txt`:

```
python-binance== 1.0.37
typer==0.15.1
pydantic==2.10.4
python-dotenv==1.0.1
streamlit==1.58.0
```