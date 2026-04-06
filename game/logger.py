import logging
import datetime
import os

logger = logging.getLogger("game_story")
logger.setLevel(logging.INFO)
logger.addHandler(logging.NullHandler())


def setup_logger():
    # Remove NullHandler if it's there
    for handler in logger.handlers:
        if isinstance(handler, logging.NullHandler):
            logger.removeHandler(handler)

    # Check if we already have a FileHandler
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return

    os.makedirs("stories", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"stories/game_story_{timestamp}.log"

    fh = logging.FileHandler(filename, encoding="utf-8")
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def log_event(event_type: str, details: str):
    logger.info(f"[{event_type}]\n{details}\n{'-' * 40}")
