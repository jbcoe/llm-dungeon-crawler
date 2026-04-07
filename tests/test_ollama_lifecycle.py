"""Unit tests for Ollama lifecycle management."""

import os
import signal
from unittest.mock import MagicMock, patch

from game.ai import AIGenerator


@patch("game.ai.ollama.list")
@patch("game.ai.ps")
@patch("game.ai.generate")
def test_manage_ollama_already_running(
    mock_generate: MagicMock, mock_ps: MagicMock, mock_list: MagicMock
) -> None:
    """If the model is already running, it should not be stopped on exit."""
    mock_list.return_value = MagicMock()
    mock_model = MagicMock()
    mock_model.model = "gemma4:e4b"
    mock_ps.return_value = MagicMock(models=[mock_model])

    with AIGenerator.manage_ollama("gemma4:e4b"):
        pass

    # Should NOT have called generate with keep_alive=0
    mock_generate.assert_not_called()


@patch("game.ai.ollama.list")
@patch("game.ai.ps")
@patch("game.ai.generate")
def test_manage_ollama_not_running(
    mock_generate: MagicMock, mock_ps: MagicMock, mock_list: MagicMock
) -> None:
    """If the model is NOT running, it should be stopped on exit."""
    mock_list.return_value = MagicMock()
    mock_ps.return_value = MagicMock(models=[])

    with AIGenerator.manage_ollama("gemma4:e4b"):
        pass

    # Should have called generate with keep_alive=0 to unload it
    mock_generate.assert_called_once_with(model="gemma4:e4b", keep_alive=0)


@patch("game.ai.ollama.list", side_effect=[Exception("Refused"), MagicMock()])
@patch("subprocess.Popen")
@patch("os.killpg")
@patch("os.getpgid")
def test_manage_ollama_starts_server(
    mock_getpgid: MagicMock,
    mock_killpg: MagicMock,
    mock_popen: MagicMock,
    mock_list: MagicMock,
) -> None:
    """If the server is not running, it should be started and then stopped."""
    mock_process = MagicMock()
    mock_process.pid = 1234
    mock_popen.return_value = mock_process
    mock_getpgid.return_value = 5678

    with patch("time.sleep"):  # Speed up the test
        with AIGenerator.manage_ollama("gemma4:e4b"):
            pass

    # Server should be started
    mock_popen.assert_called_once()
    assert "ollama" in mock_popen.call_args[0][0]
    assert "serve" in mock_popen.call_args[0][0]

    # Server should be stopped via SIGTERM to process group
    if hasattr(os, "killpg"):
        mock_killpg.assert_called_once_with(5678, signal.SIGTERM)
    else:
        mock_process.terminate.assert_called_once()
