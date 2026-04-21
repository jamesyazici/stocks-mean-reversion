import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "bot.log")
_initialized = False


def get_logger(name: str = "bot") -> logging.Logger:
    """Return a logger that writes to both console and logs/bot.log."""
    global _initialized

    logger = logging.getLogger(name)

    if not _initialized:
        os.makedirs(_LOG_DIR, exist_ok=True)

        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console = logging.StreamHandler()
        console.setFormatter(fmt)

        # Rotating file handler — keeps last 5 MB of logs
        file_handler = RotatingFileHandler(
            _LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        file_handler.setFormatter(fmt)

        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(console)
        root.addHandler(file_handler)

        _initialized = True

    return logger
