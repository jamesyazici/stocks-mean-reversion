from datetime import datetime, timezone, timedelta
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from config import ALPACA_API_KEY, ALPACA_SECRET_KEY, TOTAL_BARS, BAR_TIMEFRAME_MINUTES

# Single shared data client (no auth required for market data on free tier,
# but providing keys enables higher rate limits)
_data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)


def fetch_bars(symbol: str, n_bars: int = TOTAL_BARS) -> pd.DataFrame:
    """Fetch the most recent n_bars 1-minute bars for a symbol.

    Returns a DataFrame with columns: open, high, low, close, volume,
    indexed by timestamp. Returns empty DataFrame on failure.
    """
    # Request a window large enough to guarantee n_bars of trading minutes
    end = datetime.now(timezone.utc)
    # Add extra calendar buffer to account for weekends/holidays
    start = end - timedelta(days=5)

    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame(BAR_TIMEFRAME_MINUTES, TimeFrameUnit.Minute),
        start=start,
        end=end,
        limit=n_bars,
    )

    bars = _data_client.get_stock_bars(request)
    df = bars.df

    if df.empty:
        return df

    # When fetching a single symbol the index is (symbol, timestamp);
    # drop the symbol level so callers get a flat timestamp index.
    if isinstance(df.index, pd.MultiIndex):
        df = df.xs(symbol, level="symbol")

    # Keep only the most recent n_bars rows
    return df.tail(n_bars)
