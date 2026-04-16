"""Unit tests for llama-server connection checking."""

from unittest.mock import MagicMock, patch

import pytest

from game.cli import check_llama_server_connection


@patch("game.cli.OpenAI")
def test_check_llama_server_connection_success(mock_openai_cls: MagicMock) -> None:
    """Verify connection check passes when llama-server is reachable."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.models.list.return_value = MagicMock()

    # Should not raise or exit
    check_llama_server_connection()

    mock_client.models.list.assert_called_once()


@patch("game.cli.OpenAI")
@patch("game.cli.console.print")
def test_check_llama_server_connection_error(
    mock_print: MagicMock, mock_openai_cls: MagicMock
) -> None:
    """Verify connection check exits and prints help when server is unreachable."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.models.list.side_effect = Exception("Connection refused")

    with pytest.raises(SystemExit) as exc_info:
        check_llama_server_connection()

    assert exc_info.value.code == 1
    mock_print.assert_called()


@patch("game.cli.OpenAI")
def test_check_llama_server_connection_custom_url(mock_openai_cls: MagicMock) -> None:
    """Verify that a custom server URL is forwarded to the OpenAI client."""
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.models.list.return_value = MagicMock()

    check_llama_server_connection("http://192.168.1.10:8080")

    # The base_url passed to OpenAI should include /v1
    call_kwargs = mock_openai_cls.call_args[1]
    assert call_kwargs["base_url"] == "http://192.168.1.10:8080/v1"
