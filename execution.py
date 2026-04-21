import math
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from config import (
    ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL,
    POSITION_SIZE_PCT, STOP_LOSS_PCT, Z_SCORE_EXIT,
)
from logger import get_logger

log = get_logger(__name__)

# Paper trading client — paper=True routes all orders to the paper endpoint
_trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)


def get_account():
    """Fetch account object (contains equity, buying power, etc.)."""
    return _trading_client.get_account()


def get_position(symbol: str):
    """Return the current open position for symbol, or None if flat."""
    try:
        return _trading_client.get_open_position(symbol)
    except Exception:
        return None


def get_all_positions() -> dict:
    """Return a dict mapping symbol -> position object for all open positions."""
    positions = _trading_client.get_all_positions()
    return {p.symbol: p for p in positions}


def place_order(symbol: str, side: OrderSide, qty: int, reason: str) -> None:
    """Place a market order and log the result."""
    if qty <= 0:
        log.warning(f"Skipping order for {symbol}: qty={qty} is non-positive.")
        return

    request = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=side,
        time_in_force=TimeInForce.DAY,
    )
    order = _trading_client.submit_order(request)
    log.info(
        f"ORDER PLACED | symbol={symbol} side={side.value} qty={qty} "
        f"reason={reason} order_id={order.id}"
    )


def close_position(symbol: str, reason: str) -> None:
    """Close the entire open position for symbol."""
    try:
        _trading_client.close_position(symbol)
        log.info(f"POSITION CLOSED | symbol={symbol} reason={reason}")
    except Exception as e:
        log.error(f"Failed to close position for {symbol}: {e}", exc_info=True)


def calculate_qty(symbol: str, price: float) -> int:
    """Calculate how many shares to buy/sell based on POSITION_SIZE_PCT of equity."""
    account = get_account()
    equity = float(account.equity)
    max_dollars = equity * POSITION_SIZE_PCT
    qty = math.floor(max_dollars / price)
    return max(qty, 0)


def should_stop_loss(position, current_price: float) -> bool:
    """Return True if current price has moved STOP_LOSS_PCT against the entry."""
    entry_price = float(position.avg_entry_price)
    qty = float(position.qty)

    if qty > 0:  # long position — stop if price falls
        return current_price <= entry_price * (1 - STOP_LOSS_PCT)
    else:  # short position — stop if price rises
        return current_price >= entry_price * (1 + STOP_LOSS_PCT)


def should_exit_on_reversion(zscore: float, position) -> bool:
    """Return True when z-score has reverted close enough to zero to take profit."""
    qty = float(position.qty)
    if qty > 0:  # long: entered when z-score was very negative
        return zscore >= -Z_SCORE_EXIT
    else:  # short: entered when z-score was very positive
        return zscore <= Z_SCORE_EXIT
