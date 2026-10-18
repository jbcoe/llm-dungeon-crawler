"""Unit tests for cli.py."""

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from game.cli import (
    check_history_length,
    check_ollama_connection,
    check_openai_connection,
    main,
)


def test_check_history_length() -> None:
    """Verify integer history limits are correctly cast and negatives raise errors."""
    assert check_history_length("100") == 100
    assert check_history_length("0") == 0

    with pytest.raises(argparse.ArgumentTypeError):
        check_history_length("-1")

    with pytest.raises(ValueError):
        check_history_length("abc")


@patch("ollama.list")
def test_check_ollama_connection_success(mock_list: MagicMock) -> None:
    """Ensure the CLI passes validation when the required Ollama model is detected."""
    # Test object response
    mock_model = MagicMock()
    mock_model.model = "gemma4:e4b"
    mock_list.return_value = MagicMock(models=[mock_model])

    # Should not raise or exit
    check_ollama_connection()


@patch("ollama.list")
@patch("game.cli.console.print")
def test_check_ollama_connection_missing_model(
    mock_print: MagicMock, mock_list: MagicMock
) -> None:
    """Verify CLI exits with an error if the required model is missing."""
    # Test dictionary response
    mock_list.return_value = {"models": [{"name": "other_model"}]}

    with pytest.raises(SystemExit) as exc_info:
        check_ollama_connection()

    assert exc_info.value.code == 1
    mock_print.assert_called()


@patch("ollama.list")
def test_check_ollama_connection_tag_neutral(mock_list: MagicMock) -> None:
    """Ensure that the CLI finds models even when :latest is implicit or explicit."""
    # Scenario 1: Model is llama3:latest, user requests llama3
    mock_model = MagicMock()
    mock_model.model = "llama3:latest"
    mock_list.return_value = MagicMock(models=[mock_model])

    # Should not raise or exit
    check_ollama_connection("llama3")

    # Scenario 2: Model is llama3, user requests llama3:latest
    mock_model.model = "llama3"
    mock_list.return_value = MagicMock(models=[mock_model])

    # Should not raise or exit
    check_ollama_connection("llama3:latest")


@patch("ollama.list", side_effect=Exception("Connection refused"))
@patch("game.cli.console.print")
def test_check_ollama_connection_error(
    mock_print: MagicMock, mock_list: MagicMock
) -> None:
    """Validate that connection exceptions print troubleshooting steps and exit."""
    with pytest.raises(SystemExit) as exc_info:
        check_ollama_connection()

    assert exc_info.value.code == 1
    mock_print.assert_called()


@patch("game.cli.safe_urlopen")
def test_check_openai_connection_success(mock_urlopen: MagicMock) -> None:
    """Accept an OpenAI-compatible endpoint advertising the requested model."""
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(
        {"data": [{"id": "other-model"}, {"id": "remote-model"}]}
    ).encode()
    mock_urlopen.return_value = response

    check_openai_connection("http://api.example/v1/", "remote-model", "test-key")

    request = mock_urlopen.call_args.args[0]
    assert request.full_url == "http://api.example/v1/models"
    assert request.get_header("Authorization") == "Bearer test-key"


@patch("game.cli.safe_urlopen")
@patch("game.cli.console.print")
def test_check_openai_connection_missing_model(
    mock_print: MagicMock, mock_urlopen: MagicMock
) -> None:
    """Exit when the requested remote model is not advertised."""
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(
        {"data": [{"id": "other-model"}]}
    ).encode()
    mock_urlopen.return_value = response

    with pytest.raises(SystemExit) as exc_info:
        check_openai_connection("http://api.example/v1", "remote-model", "test-key")

    assert exc_info.value.code == 1
    mock_print.assert_called()


@patch("sys.argv", ["dungeon-crawler", "--history-length", "50"])
@patch("game.cli.AIGenerator.manage_ollama")
@patch("game.cli.check_ollama_connection")
@patch("game.cli.GameEngine")
def test_main(
    mock_engine_cls: MagicMock, mock_check_conn: MagicMock, mock_manage: MagicMock
) -> None:
    """Ensure the CLI entry point correctly parses arguments and launches the engine."""
    mock_engine = mock_engine_cls.return_value
    mock_manage.return_value.__enter__.return_value = None

    main()

    mock_manage.assert_called_once_with("gemma4:e4b")
    mock_check_conn.assert_called_once_with("gemma4:e4b")
    mock_engine_cls.assert_called_once_with(
        max_history=50, model="gemma4:e4b", map_size=8, max_loading_time=0.0
    )
    mock_engine.start.assert_called_once()


@patch(
    "sys.argv",
    ["dungeon-crawler", "--experimental-max-loading-time", "3.5"],
)
@patch("game.cli.AIGenerator.manage_ollama")
@patch("game.cli.check_ollama_connection")
@patch("game.cli.GameEngine")
def test_main_with_loading_time(
    mock_engine_cls: MagicMock, mock_check_conn: MagicMock, mock_manage: MagicMock
) -> None:
    """Ensure --experimental-max-loading-time is passed to the game engine."""
    mock_engine = mock_engine_cls.return_value
    mock_manage.return_value.__enter__.return_value = None

    main()

    mock_engine_cls.assert_called_once_with(
        max_history=1000, model="gemma4:e4b", map_size=8, max_loading_time=3.5
    )
    mock_engine.start.assert_called_once()


@patch(
    "sys.argv",
    [
        "dungeon-crawler",
        "--backend",
        "openai",
        "--base-url",
        "http://api.example/v1",
        "--model",
        "remote-model",
    ],
)
@patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}, clear=True)
@patch("game.cli.AIGenerator.manage_ollama")
@patch("game.cli.check_openai_connection")
@patch("game.cli.GameEngine")
@patch("game.cli.AIGenerator")
def test_main_with_openai_backend(
    mock_ai_cls: MagicMock,
    mock_engine_cls: MagicMock,
    mock_check_conn: MagicMock,
    mock_manage: MagicMock,
) -> None:
    """Configure the engine to use an OpenAI-compatible remote backend."""
    mock_ai = mock_ai_cls.return_value
    mock_engine = mock_engine_cls.return_value

    main()

    mock_manage.assert_not_called()
    mock_check_conn.assert_called_once_with(
        "http://api.example/v1", "remote-model", "env-key"
    )
    mock_ai_cls.assert_called_once_with(
        model="remote-model",
        backend="openai",
        base_url="http://api.example/v1",
        api_key="env-key",
    )
    mock_engine_cls.assert_called_once_with(
        max_history=1000,
        model="remote-model",
        ai_generator=mock_ai,
        map_size=8,
        max_loading_time=0.0,
    )
    mock_engine.start.assert_called_once()
