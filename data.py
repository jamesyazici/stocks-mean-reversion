from datetime import datetime, timezone, timedelta
import pandas as pd
import yfinance as yf
from config import TOTAL_BARS, BAR_TIMEFRAME_MINUTES
from logger import get_logger

log = get_logger(__name__)


def fetch_bars(symbol: str, n_bars: int = TOTAL_BARS) -> pd.DataFrame:
    """Fetch the most recent n_bars 1-minute bars for a symbol using yfinance.

    Returns a DataFrame with lowercase columns (open, high, low, close, volume)
    indexed by timestamp. Returns an empty DataFrame on failure.
    """
    # 5 calendar days is enough to collect 90 trading minutes even across weekends
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=5)

    interval = f"{BAR_TIMEFRAME_MINUTES}m"

    try:
        df = yf.download(
            tickers=symbol,
            start=start,
            end=end,
            interval=interval,
            progress=False,
            auto_adjust=True,  # adjusts for splits/dividends automatically
        )
    except Exception as e:
        log.error(f"{symbol} | yfinance download failed: {e}", exc_info=True)
        return pd.DataFrame()

    if df is None or df.empty:
        log.warning(f"{symbol} | yfinance returned no data.")
        return pd.DataFrame()

    # yfinance returns MultiIndex columns when auto_adjust=True in some versions;
    # flatten to a single level and lowercase all column names.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]

    # Ensure the required column is present after normalisation
    if "close" not in df.columns:
        log.warning(f"{symbol} | 'close' column missing after normalisation. Columns: {list(df.columns)}")
        return pd.DataFrame()

    return df.tail(n_bars)


def fetch_latest_price(symbol: str) -> float | None:
    """Return the latest traded price for a symbol using yfinance fast_info.

    Returns None if the price cannot be retrieved.
    """
    try:
        info = yf.Ticker(symbol).fast_info
        price = info.last_price
        if price is None or price != price:  # catch None and NaN
            log.warning(f"{symbol} | fast_info returned no valid price.")
            return None
        return float(price)
    except Exception as e:
        log.error(f"{symbol} | fast_info lookup failed: {e}", exc_info=True)
        return None
