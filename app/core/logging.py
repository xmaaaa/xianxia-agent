import logging
import sys
from pathlib import Path

from app.core.config import PROJECT_ROOT

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE = PROJECT_ROOT / "app.log"


def setup_logging() -> None:
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.WARNING)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)

    app_logger = logging.getLogger("app")
    app_logger.handlers.clear()
    app_logger.setLevel(logging.WARNING)
    app_logger.addHandler(file_handler)
    app_logger.addHandler(console_handler)

    for noisy in ("httpcore", "httpx", "urllib3", "chromadb", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.ERROR)
