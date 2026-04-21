"""Tests that Alpaca credentials load correctly and a live connection works."""
import pytest
from alpaca.trading.client import TradingClient
import config


def test_credentials_loaded():
    """Credentials must be non-empty strings after loading from .env."""
    assert config.ALPACA_API_KEY, "APCA_API_KEY_ID is missing or empty"
    assert config.ALPACA_SECRET_KEY, "APCA_API_SECRET_KEY is missing or empty"


def test_alpaca_connection():
    """Verify we can authenticate and fetch account info from Alpaca paper trading."""
    client = TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY, paper=True)
    account = client.get_account()

    # A valid response always has a non-empty account ID
    assert account.id, "Account ID should not be empty"
    assert float(account.equity) >= 0, "Equity should be a non-negative number"


def test_market_clock():
    """Verify the clock endpoint returns a valid response."""
    client = TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY, paper=True)
    clock = client.get_clock()

    assert hasattr(clock, "is_open"), "Clock response missing 'is_open' field"
    assert hasattr(clock, "next_open"), "Clock response missing 'next_open' field"
