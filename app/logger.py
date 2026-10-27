import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name="lostfound"):
    logger = logging.getLogger(name)
    if not logger.handlers:                 # avoid adding the handler twice
        Path("logs").mkdir(exist_ok=True)
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler("logs/app.log", maxBytes=1_000_000,
                                      backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger