"""Unit tests for game/theme.py logic."""

from pathlib import Path

import pytest

from game.theme import (
    PROMPT_REQUIRED_FIELDS,
    Theme,
    _validate_data_file,
    _validate_prompt_file,
    validate_theme,
)

# ---------------------------------------------------------------------------
# _validate_data_file
# ---------------------------------------------------------------------------


def test_validate_data_file_valid(tmp_path: Path) -> None:
    """A well-formed data file produces no errors."""
    f = tmp_path / "enemies.md"
    f.write_text("# Enemy Types\n\n- Goblin: Small and mean\n- Dragon: Big and mean\n")
    assert _validate_data_file(f) == []


def test_validate_data_file_asterisk_bullet(tmp_path: Path) -> None:
    """Asterisk-prefixed bullets are also valid."""
    f = tmp_path / "items.md"
    f.write_text("* Laser Sword: Cuts things\n")
    assert _validate_data_file(f) == []


def test_validate_data_file_no_entries_ok(tmp_path: Path) -> None:
    """A file with no entries (only comments/whitespace) is valid."""
    f = tmp_path / "rooms.md"
    f.write_text("# Rooms\n\nThis file has no list entries.\n")
    assert _validate_data_file(f) == []


def test_validate_data_file_malformed_line(tmp_path: Path) -> None:
    """A line that looks like an entry but is missing the colon is flagged."""
    f = tmp_path / "npcs.md"
    f.write_text("- Merchant missing colon here\n")
    errors = _validate_data_file(f)
    assert any("unexpected format" in e for e in errors)


def test_validate_data_file_missing_file(tmp_path: Path) -> None:
    """A file that cannot be read produces a read error."""
    missing = tmp_path / "ghost.md"
    errors = _validate_data_file(missing)
    assert any("cannot read file" in e for e in errors)


# ---------------------------------------------------------------------------
# _validate_prompt_file
# ---------------------------------------------------------------------------


def test_validate_prompt_file_valid(tmp_path: Path) -> None:
    """A prompt file with exactly the right variables produces no errors."""
    f = tmp_path / "rest.md"
    required = PROMPT_REQUIRED_FIELDS["rest.md"]
    f.write_text("HP: {player_hp}/{player_max_hp}. Rest now.")
    assert _validate_prompt_file(f, required) == []


def test_validate_prompt_file_missing_variable(tmp_path: Path) -> None:
    """A prompt file missing a required variable is flagged."""
    f = tmp_path / "rest.md"
    required = PROMPT_REQUIRED_FIELDS["rest.md"]
    # Only includes player_hp, not player_max_hp
    f.write_text("HP: {player_hp}. Rest.")
    errors = _validate_prompt_file(f, required)
    assert any("player_max_hp" in e and "missing" in e for e in errors)


def test_validate_prompt_file_extra_variable(tmp_path: Path) -> None:
    """A prompt file with an unexpected variable is flagged."""
    f = tmp_path / "rest.md"
    required = PROMPT_REQUIRED_FIELDS["rest.md"]
    f.write_text("HP: {player_hp}/{player_max_hp}. Also {foo}.")
    errors = _validate_prompt_file(f, required)
    assert any("foo" in e and "unexpected" in e for e in errors)


def test_validate_prompt_file_no_variables_required(tmp_path: Path) -> None:
    """intro.md requires no variables; any placeholder is an error."""
    f = tmp_path / "intro.md"
    required = PROMPT_REQUIRED_FIELDS["intro.md"]
    f.write_text("You are a {hero} entering the dungeon.")
    errors = _validate_prompt_file(f, required)
    assert any("hero" in e and "unexpected" in e for e in errors)


def test_validate_prompt_file_intro_no_variables_ok(tmp_path: Path) -> None:
    """intro.md with no placeholders is valid."""
    f = tmp_path / "intro.md"
    required = PROMPT_REQUIRED_FIELDS["intro.md"]
    f.write_text("You step into the darkness.")
    assert _validate_prompt_file(f, required) == []


def test_validate_prompt_file_missing_file(tmp_path: Path) -> None:
    """A prompt file that cannot be read returns a read error."""
    missing = tmp_path / "ghost.md"
    errors = _validate_prompt_file(missing, frozenset())
    assert any("cannot read file" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_theme (integration)
# ---------------------------------------------------------------------------


def test_validate_theme_empty_dir_errors(tmp_path: Path) -> None:
    """An empty theme directory produces errors for all missing files."""
    errors = validate_theme(tmp_path)
    assert len(errors) > 0
    assert any("missing required data file: enemies.md" in e for e in errors)
    assert any("missing required 'prompts' subdirectory" in e for e in errors)


def test_validate_theme_missing_prompts_dir_exhaustive(tmp_path: Path) -> None:
    """When the prompts dir is missing, all individual files are still reported."""
    # Data files are present
    for f in ["enemies.md", "items.md", "npcs.md", "rooms.md"]:
        (tmp_path / f).write_text("- Name: Desc\n")

    errors = validate_theme(tmp_path)
    assert any("missing required 'prompts' subdirectory" in e for e in errors)
    # All 6 prompt files should be reported as missing
    assert any("prompts/combat.md" in e for e in errors)
    assert any("prompts/intro.md" in e for e in errors)
    assert any("prompts/item_use.md" in e for e in errors)
    assert any("prompts/npc.md" in e for e in errors)
    assert any("prompts/rest.md" in e for e in errors)
    assert any("prompts/room.md" in e for e in errors)


def test_validate_theme_invalid_data_file(tmp_path: Path) -> None:
    """A malformed data file causes validate_theme to return errors."""
    (tmp_path / "enemies.md").write_text("This line has no colon at all\n")
    errors = validate_theme(tmp_path)
    assert len(errors) > 0


def test_validate_theme_invalid_prompt(tmp_path: Path) -> None:
    """A prompt with the wrong variables causes errors."""
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "rest.md").write_text("Rest now. {unknown_var}")
    errors = validate_theme(tmp_path)
    assert any("unknown_var" in e for e in errors)
    assert any("player_hp" in e and "missing" in e for e in errors)


def test_validate_theme_scifi_theme() -> None:
    """The bundled sci-fi theme directory passes validation without errors."""
    scifi_dir = Path(__file__).parent.parent / "themes" / "scifi"
    assert scifi_dir.is_dir(), f"sci-fi theme dir not found at {scifi_dir}"
    errors = validate_theme(scifi_dir)
    assert errors == [], "Sci-fi theme validation failed:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# Theme (class)
# ---------------------------------------------------------------------------


def test_theme_from_path(tmp_path: Path) -> None:
    """Verify that a valid theme can be loaded from a path."""
    theme_path = tmp_path / "mytheme"
    theme_path.mkdir()

    for f in ["enemies.md", "items.md", "npcs.md", "rooms.md"]:
        (theme_path / f).write_text("- Name: Description\n")

    prompts_dir = theme_path / "prompts"
    prompts_dir.mkdir()
    for f, fields in PROMPT_REQUIRED_FIELDS.items():
        content = "".join([f"{{{field}}}" for field in fields])
        (prompts_dir / f).write_text(content)

    theme = Theme.from_path(theme_path)

    assert theme.name == "mytheme"
    assert theme.path == theme_path
    assert len(theme.enemies) == 1
    assert theme.enemies[0]["name"] == "Name"
    assert "{player_hp}" in theme.rest_prompt


def test_theme_from_path_invalid_raises(tmp_path: Path) -> None:
    """Loading an invalid theme raises ValueError."""
    theme_path = tmp_path / "badtheme"
    theme_path.mkdir()
    # Incomplete theme
    with pytest.raises(ValueError, match="missing required data file"):
        Theme.from_path(theme_path)
