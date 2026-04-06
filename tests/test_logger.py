"""Unit tests for logger.py."""

import logging
import os
from unittest.mock import patch

from game.logger import log_event, logger, setup_logger


def test_setup_logger() -> None:
    """Verify that setup_logger initializes a FileHandler correctly and idempotently."""
    # Remove existing FileHandlers
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)

    # First call - patch os.makedirs and use a mock object for FileHandler
    # to avoid patching the class itself
    with (
        patch("os.makedirs") as mock_makedirs,
        patch("game.logger.logging.FileHandler") as mock_fh,
    ):
        setup_logger()
        mock_makedirs.assert_called_once_with("stories", exist_ok=True)
        mock_fh.assert_called()

    # Second call - we can add a real FileHandler to see the early exit
    fake_handler = logging.FileHandler(os.devnull, delay=True)
    logger.addHandler(fake_handler)

    with patch("os.makedirs") as mock_makedirs:
        setup_logger()
        mock_makedirs.assert_not_called()

    logger.removeHandler(fake_handler)


def test_log_event() -> None:
    """Ensure logging events pass both category and details into the logger backend."""
    with patch.object(logger, "info") as mock_info:
        log_event("TEST_EVENT", "Test Details")
        mock_info.assert_called_once()
        args = mock_info.call_args[0][0]
        assert "TEST_EVENT" in args
        assert "Test Details" in args
