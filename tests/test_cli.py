"""Unit tests for cli.py."""

import argparse
from unittest.mock import MagicMock, patch

import pytest

from game.cli import check_history_length, check_llama_server_connection, main


def test_check_history_length() -> None:
    """Verify integer history limits are correctly cast and negatives raise errors."""
    assert check_history_length("100") == 100
    assert check_history_length("0") == 0

    with pytest.raises(argparse.ArgumentTypeError):
        check_history_length("-1")

    with pytest.raises(ValueError):
        check_history_length("abc")


@patch("game.cli.OpenAI")
def test_check_llama_server_connection_success(mock_openai_cls: MagicMock) -> None:
    """Ensure the CLI passes validation when llama-server is reachable."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.models.list.return_value = MagicMock()

    # Should not raise or exit
    check_llama_server_connection()


@patch("game.cli.OpenAI")
@patch("game.cli.console.print")
def test_check_llama_server_connection_error(
    mock_print: MagicMock, mock_openai_cls: MagicMock
) -> None:
    """Validate that connection exceptions print troubleshooting steps and exit."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.models.list.side_effect = Exception("Connection refused")

    with pytest.raises(SystemExit) as exc_info:
        check_llama_server_connection()

    assert exc_info.value.code == 1
    mock_print.assert_called()


@patch("sys.argv", ["dungeon-crawler", "--history-length", "50"])
@patch("game.cli.check_llama_server_connection")
@patch("game.cli.GameEngine")
def test_main(mock_engine_cls: MagicMock, mock_check_conn: MagicMock) -> None:
    """Ensure the CLI entry point correctly parses arguments and launches the engine."""
    mock_engine = mock_engine_cls.return_value

    main()

    mock_check_conn.assert_called_once_with("http://localhost:8080")
    mock_engine_cls.assert_called_once_with(
        max_history=50,
        model="default",
        server_url="http://localhost:8080",
        map_size=8,
        max_loading_time=0.0,
    )
    mock_engine.start.assert_called_once()


@patch(
    "sys.argv",
    ["dungeon-crawler", "--experimental-max-loading-time", "3.5"],
)
@patch("game.cli.check_llama_server_connection")
@patch("game.cli.GameEngine")
def test_main_with_loading_time(
    mock_engine_cls: MagicMock, mock_check_conn: MagicMock
) -> None:
    """Ensure --experimental-max-loading-time is passed to the game engine."""
    mock_engine = mock_engine_cls.return_value

    main()

    mock_engine_cls.assert_called_once_with(
        max_history=1000,
        model="default",
        server_url="http://localhost:8080",
        map_size=8,
        max_loading_time=3.5,
    )
    mock_engine.start.assert_called_once()


@patch(
    "sys.argv",
    ["dungeon-crawler", "--server-url", "http://my-server:9090"],
)
@patch("game.cli.check_llama_server_connection")
@patch("game.cli.GameEngine")
def test_main_with_custom_server_url(
    mock_engine_cls: MagicMock, mock_check_conn: MagicMock
) -> None:
    """Ensure --server-url is forwarded to both the connection check and the engine."""
    mock_engine = mock_engine_cls.return_value

    main()

    mock_check_conn.assert_called_once_with("http://my-server:9090")
    mock_engine_cls.assert_called_once_with(
        max_history=1000,
        model="default",
        server_url="http://my-server:9090",
        map_size=8,
        max_loading_time=0.0,
    )
    mock_engine.start.assert_called_once()
