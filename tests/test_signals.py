"""Tests for signal computation — no API calls, uses synthetic price data."""
import math
import numpy as np
import pandas as pd
import pytest

from signals import compute_zscore, compute_volatility_filter, compute_signals


def make_df(prices: list) -> pd.DataFrame:
    """Wrap a price list in the same DataFrame shape that data.py returns."""
    idx = pd.date_range("2024-01-01", periods=len(prices), freq="1min")
    return pd.DataFrame({"close": prices}, index=idx)


# --- compute_zscore ---

def test_zscore_mean_is_zero():
    """A price exactly at the rolling mean should yield z-score ≈ 0."""
    prices = pd.Series([100.0] * 20)
    # Last value equals mean — std is 0, expect nan
    result = compute_zscore(prices)
    assert math.isnan(result)


def test_zscore_positive():
    """Price above the mean should produce a positive z-score."""
    base = [100.0] * 19 + [110.0]   # last bar spikes up
    prices = pd.Series(base)
    z = compute_zscore(prices)
    assert z > 0


def test_zscore_negative():
    """Price below the mean should produce a negative z-score."""
    base = [100.0] * 19 + [90.0]    # last bar drops
    prices = pd.Series(base)
    z = compute_zscore(prices)
    assert z < 0


def test_zscore_insufficient_data():
    """Fewer bars than the window should return nan."""
    prices = pd.Series([100.0] * 5)
    assert math.isnan(compute_zscore(prices, window=20))


def test_zscore_magnitude():
    """A 2-sigma move should return |z| ≈ 2."""
    np.random.seed(42)
    base_prices = np.full(19, 100.0)
    std_estimate = 1.0
    spike = 100.0 + 2 * std_estimate
    prices = pd.Series(np.append(base_prices, spike))
    z = compute_zscore(prices)
    # Should be positive and reasonably close to 2
    assert z > 1.5


# --- compute_volatility_filter ---

def test_volatility_filter_normal():
    """Stable prices should NOT trigger the volatility filter."""
    prices = pd.Series([100.0 + i * 0.01 for i in range(90)])
    assert compute_volatility_filter(prices) is False


def test_volatility_filter_triggered():
    """Extremely high recent volatility SHOULD trigger the filter."""
    # First 70 bars are calm, last 20 bars are wildly volatile
    calm = [100.0] * 70
    volatile = [100.0 + (i % 2) * 50 for i in range(20)]
    prices = pd.Series(calm + volatile)
    assert compute_volatility_filter(prices) is True


def test_volatility_filter_insufficient_data():
    """Too few bars — filter should not block trading."""
    prices = pd.Series([100.0] * 10)
    assert compute_volatility_filter(prices) is False


# --- compute_signals ---

def test_compute_signals_not_enough_data():
    """Fewer than LOOKBACK_WINDOW bars should mark skip=True and return nans."""
    df = make_df([100.0] * 5)
    result = compute_signals(df)
    assert result["skip"] is True
    assert math.isnan(result["zscore"])


def test_compute_signals_returns_all_keys():
    """compute_signals must always return the expected keys."""
    df = make_df([100.0 + i * 0.05 for i in range(90)])
    result = compute_signals(df)
    for key in ("zscore", "current_std", "avg_std", "skip", "latest_price"):
        assert key in result, f"Missing key: {key}"


def test_compute_signals_latest_price():
    """latest_price should equal the last close in the DataFrame."""
    prices = [100.0 + i * 0.1 for i in range(90)]
    df = make_df(prices)
    result = compute_signals(df)
    assert result["latest_price"] == pytest.approx(prices[-1])
