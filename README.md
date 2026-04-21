# Mean Reversion Paper Trading Bot

A simple automated paper trading bot built as a learning project — my first step moving from prediction markets into actual financial markets. No real money involved, just a clean way to learn how algorithmic trading systems are structured and how strategies perform in live market conditions.

Built with Python and the Alpaca API.

---

## What It Does

The bot runs every 60 seconds during market hours, watches a small list of stocks (SPY, MSFT, AAPL by default), and decides whether to place a trade based on a mean reversion signal. All trades go through Alpaca's paper trading environment, so everything is simulated with fake money.

Every cycle it:
- Fetches the latest 90 one-minute bars per stock
- Computes a z-score to measure how far the current price is from its recent average
- Enters a trade if the price is unusually far from the mean
- Exits when the price reverts back toward the mean, or cuts the loss if it moves too far the wrong way
- Logs everything to the console and to `logs/bot.log`

---

## The Strategy (Simply Explained)

**Mean reversion** is the idea that prices tend to drift back toward their historical average after moving too far in either direction.

If a stock's price drops sharply below its recent average (z-score below -2.0), the bot buys it, betting it will bounce back up. If the price spikes well above the average (z-score above +2.0), the bot short-sells it, betting it will come back down. Once the price returns close to the mean (z-score within 0.5 of zero), the position is closed and the profit is taken.

A volatility filter is also in place: if a stock is moving unusually erratically compared to its own history (current std > 2x its 90-bar average), the bot skips it entirely for that cycle to avoid getting caught in chaotic price action.

There's also a hard stop loss at 3% — if a position moves 3% against entry, it's closed immediately regardless of z-score.

**Key parameters** (all in `config.py`):

| Parameter | Default | Description |
|---|---|---|
| Z-score entry threshold | ±2.0 | How far from mean before entering |
| Z-score exit threshold | 0.5 | How close to mean before exiting |
| Lookback window | 20 bars | Rolling window for mean/std |
| Stop loss | 3% | Max loss before forced exit |
| Position size | 10% of equity | Max allocation per trade |
| Bar timeframe | 1 minute | Granularity of price data |

---

## Setup

**1. Clone and create a virtual environment**

```bash
git clone <your-repo-url>
cd testimplementation
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure your Alpaca credentials**

Sign up for a free paper trading account at [alpaca.markets](https://alpaca.markets), then copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```
APCA_API_KEY_ID=your_key_here
APCA_API_SECRET_KEY=your_secret_here
APCA_BASE_URL=https://paper-api.alpaca.markets
```

**4. Run the tests**

Check that your credentials work and the signal logic is correct:

```bash
pytest tests/test_connection.py -v   # hits Alpaca's API
pytest tests/test_signals.py -v      # purely offline, no API needed
```

**5. Start the bot**

```bash
python bot.py
```

The bot will detect whether the market is open. If it's closed, it waits and checks again every 60 seconds. Logs are written to `logs/bot.log`.

---

## Project Structure

```
├── bot.py              Main trading loop
├── config.py           All parameters and credential loading
├── data.py             Alpaca data fetching
├── signals.py          Z-score and volatility filter logic
├── execution.py        Order placement and position management
├── logger.py           Console + rotating file logger
├── tests/
│   ├── test_connection.py   API connectivity tests
│   └── test_signals.py      Signal logic tests (no API)
├── logs/
│   └── bot.log         Written at runtime
├── .env                Your credentials (never commit this)
└── .env.example        Template showing required variable names
```

---

## Disclaimer

This project is purely experimental and educational. It runs on paper trading only — no real money is ever used or at risk. Nothing here should be taken as financial advice. Mean reversion is a real strategy used in quantitative finance, but this implementation is intentionally simple and is not optimized or validated for live trading. Use it to learn, not to trade.
