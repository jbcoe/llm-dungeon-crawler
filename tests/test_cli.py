"""Unit tests for cli.py."""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from game.cli import (
    check_history_length,
    check_ollama_connection,
    check_theme,
    main,
)
from game.theme import Theme


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


@patch("sys.argv", ["dungeon-crawler", "--history-length", "50"])
@patch("game.cli.AIGenerator.manage_ollama")
@patch("game.cli.check_ollama_connection")
@patch("game.cli.Theme.from_path")
@patch("game.cli.GameEngine")
def test_main(
    mock_engine_cls: MagicMock,
    mock_theme_from_path: MagicMock,
    mock_check_conn: MagicMock,
    mock_manage: MagicMock,
) -> None:
    """Ensure the CLI entry point correctly parses arguments and launches the engine."""
    mock_engine = mock_engine_cls.return_value
    mock_manage.return_value.__enter__.return_value = None
    mock_theme = MagicMock(spec=Theme)
    mock_theme_from_path.return_value = mock_theme

    main()

    mock_manage.assert_called_once_with("gemma4:e4b")
    mock_check_conn.assert_called_once_with("gemma4:e4b")
    mock_engine_cls.assert_called_once_with(
        max_history=50,
        model="gemma4:e4b",
        map_size=8,
        max_loading_time=0.0,
        theme=mock_theme,
    )
    mock_engine.start.assert_called_once()


@patch(
    "sys.argv",
    ["dungeon-crawler", "--experimental-max-loading-time", "3.5"],
)
@patch("game.cli.AIGenerator.manage_ollama")
@patch("game.cli.check_ollama_connection")
@patch("game.cli.Theme.from_path")
@patch("game.cli.GameEngine")
def test_main_with_loading_time(
    mock_engine_cls: MagicMock,
    mock_theme_from_path: MagicMock,
    mock_check_conn: MagicMock,
    mock_manage: MagicMock,
) -> None:
    """Ensure --experimental-max-loading-time is passed to the game engine."""
    mock_engine = mock_engine_cls.return_value
    mock_manage.return_value.__enter__.return_value = None
    mock_theme = MagicMock(spec=Theme)
    mock_theme_from_path.return_value = mock_theme

    main()

    mock_engine_cls.assert_called_once_with(
        max_history=1000,
        model="gemma4:e4b",
        map_size=8,
        max_loading_time=3.5,
        theme=mock_theme,
    )
    mock_engine.start.assert_called_once()


def test_check_theme_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify check_theme returns an absolute Path for an existing theme in themes/."""
    monkeypatch.chdir(tmp_path)
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()
    (themes_dir / "mytheme").mkdir()

    result = check_theme("mytheme")
    assert result == (tmp_path / "themes/mytheme").absolute()
    assert isinstance(result, Path)


def test_check_theme_invalid() -> None:
    """Verify check_theme raises ArgumentTypeError for a nonexistent theme."""
    with pytest.raises(argparse.ArgumentTypeError):
        check_theme("nonexistent-theme")


@patch("game.cli.AIGenerator.manage_ollama")
@patch("game.cli.check_ollama_connection")
@patch("game.cli.Theme.from_path")
@patch("game.cli.GameEngine")
def test_main_with_theme(
    mock_engine_cls: MagicMock,
    mock_theme_from_path: MagicMock,
    mock_check_conn: MagicMock,
    mock_manage: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure --theme is parsed and forwarded to the game engine."""
    monkeypatch.chdir(tmp_path)
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()
    theme_path = themes_dir / "mytheme"
    theme_path.mkdir()

    # Create a complete (valid) theme so main() doesn't exit(1) early
    for f in ["enemies.md", "items.md", "npcs.md", "rooms.md"]:
        (theme_path / f).write_text("- Name: Desc\n")
    prompts_dir = theme_path / "prompts"
    prompts_dir.mkdir()
    for f in ["combat.md", "intro.md", "item_use.md", "npc.md", "rest.md", "room.md"]:
        # Write minimal templates matching PROMPT_REQUIRED_FIELDS
        if f == "room.md":
            content = (
                "{previous_context}{room_type_name}{room_type_desc}"
                "{exits_str}{enemies_str}{npcs_str}{items_str}"
            )
        elif f == "combat.md":
            content = "{player_action}{enemy_name}{damage_dealt}{enemy_hp}{player_hp}"
        elif f == "item_use.md":
            content = "{item_name}{item_description}{room_context}"
        elif f == "npc.md":
            content = "{npc_name}{npc_context}{history}{player_message}"
        elif f == "rest.md":
            content = "{player_hp}{player_max_hp}"
        else:  # intro.md
            content = "intro"
        (prompts_dir / f).write_text(content)

    mock_engine = mock_engine_cls.return_value
    mock_manage.return_value.__enter__.return_value = None
    mock_theme = MagicMock(spec=Theme)
    mock_theme_from_path.return_value = mock_theme

    with patch("sys.argv", ["dungeon-crawler", "--theme", "mytheme"]):
        main()

    mock_engine_cls.assert_called_once_with(
        max_history=1000,
        model="gemma4:e4b",
        map_size=8,
        max_loading_time=0.0,
        theme=mock_theme,
    )
    mock_engine.start.assert_called_once()


@patch("game.cli.AIGenerator.manage_ollama")
@patch("game.cli.check_ollama_connection")
@patch("game.cli.GameEngine")
def test_main_with_theme_validation_error(
    mock_engine_cls: MagicMock,
    mock_check_conn: MagicMock,
    mock_manage: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure a theme with invalid files causes exit before the engine starts."""
    monkeypatch.chdir(tmp_path)
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()
    theme_path = themes_dir / "badtheme"
    theme_path.mkdir()

    # Write a data file with no valid entries to trigger validation failure
    (theme_path / "enemies.md").write_text("this line has no colon format at all\n")

    with patch("sys.argv", ["dungeon-crawler", "--theme", "badtheme"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    mock_engine_cls.assert_not_called()
