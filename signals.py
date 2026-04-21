import pandas as pd
from config import LOOKBACK_WINDOW, TOTAL_BARS, Z_SCORE_THRESHOLD, VOLATILITY_FILTER_MULTIPLIER


def compute_zscore(prices: pd.Series, window: int = LOOKBACK_WINDOW) -> float:
    """Return the z-score of the latest price relative to the rolling window."""
    if len(prices) < window:
        return float("nan")

    rolling_mean = prices.rolling(window).mean().iloc[-1]
    rolling_std = prices.rolling(window).std().iloc[-1]

    if rolling_std == 0:
        return float("nan")

    return (prices.iloc[-1] - rolling_mean) / rolling_std


def compute_volatility_filter(prices: pd.Series, window: int = LOOKBACK_WINDOW) -> bool:
    """Return True if the stock should be SKIPPED due to unusually high volatility.

    Compares the current rolling std (last `window` bars) against the average
    std computed over all available bars. If the current std is more than
    VOLATILITY_FILTER_MULTIPLIER times the long-run average, skip the stock.
    """
    if len(prices) < window + 1:
        return False  # Not enough data to apply filter; allow trading

    rolling_std_series = prices.rolling(window).std().dropna()

    if rolling_std_series.empty:
        return False

    current_std = rolling_std_series.iloc[-1]
    avg_std = rolling_std_series.mean()  # average over all available windows

    if avg_std == 0:
        return False

    return bool(current_std > VOLATILITY_FILTER_MULTIPLIER * avg_std)


def compute_signals(df: pd.DataFrame) -> dict:
    """Compute all signals for a single stock given its bar DataFrame.

    Returns a dict with keys:
        zscore        — latest z-score (float | nan)
        current_std   — std of the last LOOKBACK_WINDOW bars
        avg_std       — mean std across all bars
        skip          — True if volatility filter triggered
        latest_price  — most recent close price
    """
    if df.empty or len(df) < LOOKBACK_WINDOW:
        return {
            "zscore": float("nan"),
            "current_std": float("nan"),
            "avg_std": float("nan"),
            "skip": True,
            "latest_price": float("nan"),
        }

    prices = df["close"]
    zscore = compute_zscore(prices)
    skip = compute_volatility_filter(prices)

    rolling_std_series = prices.rolling(LOOKBACK_WINDOW).std().dropna()
    current_std = rolling_std_series.iloc[-1] if not rolling_std_series.empty else float("nan")
    avg_std = rolling_std_series.mean() if not rolling_std_series.empty else float("nan")

    return {
        "zscore": zscore,
        "current_std": current_std,
        "avg_std": avg_std,
        "skip": skip,
        "latest_price": prices.iloc[-1],
    }
