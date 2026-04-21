import os
from dotenv import load_dotenv

load_dotenv()

# --- Stock universe ---
STOCKS = ["SPY", "MSFT", "AAPL"]

# --- Strategy parameters ---
Z_SCORE_THRESHOLD = 2.0       # Enter trade when |z-score| exceeds this
Z_SCORE_EXIT = 0.5            # Close trade when |z-score| falls within this of zero
LOOKBACK_WINDOW = 20          # Bars used for rolling mean/std
STOP_LOSS_PCT = 0.03          # 3% stop loss against entry price
POSITION_SIZE_PCT = 0.10      # Max 10% of portfolio per position
BAR_TIMEFRAME_MINUTES = 1     # Bar size in minutes
TOTAL_BARS = 90               # Total bars to fetch per cycle (covers volatility filter)
VOLATILITY_FILTER_MULTIPLIER = 2.0  # Skip stock if current std > this * 90-bar avg std
LOOP_INTERVAL_SECONDS = 60    # How often the main loop runs

# --- Alpaca credentials (loaded from .env) ---
ALPACA_API_KEY = os.getenv("APCA_API_KEY_ID")
ALPACA_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
# Strip trailing /v2 if present — alpaca-py expects the base URL without it
_raw_url = os.getenv("APCA_BASE_URL", "https://paper-api.alpaca.markets")
ALPACA_BASE_URL = _raw_url.rstrip("/v2").rstrip("/")

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    raise EnvironmentError("Alpaca API credentials not found. Check your .env file.")
