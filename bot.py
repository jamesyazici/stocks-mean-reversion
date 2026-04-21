import time
import math
import traceback
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide

import config
from data import fetch_bars
from signals import compute_signals
from execution import (
    get_position,
    place_order,
    close_position,
    calculate_qty,
    should_stop_loss,
    should_exit_on_reversion,
)
from logger import get_logger

log = get_logger("bot")

# Trading client used only for market clock checks
_trading_client = TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY, paper=True)


def is_market_open() -> bool:
    """Return True if the US stock market is currently open."""
    clock = _trading_client.get_clock()
    return clock.is_open


def process_symbol(symbol: str) -> None:
    """Run the full signal-check-and-trade cycle for a single symbol."""
    df = fetch_bars(symbol)
    if df.empty:
        log.warning(f"{symbol} | No bar data returned, skipping.")
        return

    signals = compute_signals(df)
    zscore = signals["zscore"]
    current_std = signals["current_std"]
    avg_std = signals["avg_std"]
    skip = signals["skip"]
    price = signals["latest_price"]

    log.info(
        f"{symbol} | price={price:.2f} z={zscore:.3f} "
        f"std={current_std:.4f} avg_std={avg_std:.4f} skip={skip}"
    )

    if math.isnan(zscore):
        log.info(f"{symbol} | z-score is NaN (not enough data), skipping.")
        return

    if skip:
        log.info(f"{symbol} | Volatility filter triggered — std is elevated. Skipping.")
        return

    position = get_position(symbol)

    # --- Manage existing position ---
    if position is not None:
        if should_stop_loss(position, price):
            close_position(symbol, reason="stop_loss")
            return

        if should_exit_on_reversion(zscore, position):
            close_position(symbol, reason="mean_reversion_complete")
            return

        log.info(f"{symbol} | Holding position. No action needed.")
        return

    # --- Look for new entry signals ---
    if zscore < -config.Z_SCORE_THRESHOLD:
        # Price is well below the mean — expect reversion upward — go long
        qty = calculate_qty(symbol, price)
        place_order(symbol, OrderSide.BUY, qty, reason=f"zscore={zscore:.3f} below -{config.Z_SCORE_THRESHOLD}")

    elif zscore > config.Z_SCORE_THRESHOLD:
        # Price is well above the mean — expect reversion downward — go short
        qty = calculate_qty(symbol, price)
        place_order(symbol, OrderSide.SELL, qty, reason=f"zscore={zscore:.3f} above +{config.Z_SCORE_THRESHOLD}")

    else:
        log.info(f"{symbol} | z-score within bounds, no trade.")


def run() -> None:
    """Main loop: check market status, iterate over stocks, repeat every 60 s."""
    log.info("=== Paper trading bot starting ===")

    while True:
        try:
            if not is_market_open():
                log.info("Market is closed. Waiting 60 seconds before next check.")
                time.sleep(config.LOOP_INTERVAL_SECONDS)
                continue

            log.info("--- Market is open. Running signal cycle. ---")

            for symbol in config.STOCKS:
                try:
                    process_symbol(symbol)
                except Exception:
                    log.error(
                        f"{symbol} | Unhandled error during processing:\n"
                        + traceback.format_exc()
                    )

            log.info(f"Cycle complete. Sleeping {config.LOOP_INTERVAL_SECONDS}s.")
            time.sleep(config.LOOP_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            log.info("Bot stopped by user (KeyboardInterrupt).")
            break
        except Exception:
            log.error("Unhandled error in main loop:\n" + traceback.format_exc())
            log.info("Sleeping 60s before retrying.")
            time.sleep(config.LOOP_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
