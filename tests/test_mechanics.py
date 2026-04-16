"""Unit tests for mechanics.py."""

from pathlib import Path
from unittest.mock import patch

from game.mechanics import generate_mechanics, load_data


def test_load_data_success() -> None:
    """Verify correctly formatted markdown lists are parsed into dicts."""
    mock_file_content = "- Item One: A test item\n- Item Two: Another item"

    # We patch importlib.resources.files to return a mock Traversable
    with patch("importlib.resources.files") as mock_files:
        mock_joinpath = mock_files.return_value.joinpath.return_value
        mock_joinpath.is_file.return_value = True
        mock_joinpath.read_text.return_value = mock_file_content

        result = load_data("test.md")

        assert len(result) == 2
        assert result[0] == {"name": "Item One", "description": "A test item"}
        assert result[1] == {"name": "Item Two", "description": "Another item"}


def test_load_data_file_not_found() -> None:
    """Ensure missing data files trigger logging explicitly and return empty list."""
    with patch("importlib.resources.files") as mock_files:
        mock_joinpath = mock_files.return_value.joinpath.return_value
        mock_joinpath.is_file.return_value = False

        result = load_data("missing.md")
        assert result == []


def test_generate_mechanics_empty_exits() -> None:
    """Verify that an empty list of exits is treated as None."""
    # When exits=[], it should generate random exits
    mechanics = generate_mechanics(floor=1, exits=[])
    assert len(mechanics["exits"]) > 0
    assert all(e in ["north", "south", "east", "west"] for e in mechanics["exits"])


@patch("game.mechanics.ENEMIES", [{"name": "Goblin", "description": "Ugly"}])
@patch("game.mechanics.NPCS", [{"name": "Merchant", "description": "Sells"}])
@patch("game.mechanics.ITEMS", [{"name": "Health Potion", "description": "Heals"}])
@patch("game.mechanics.ROOMS", [{"name": "Cave", "description": "Dark"}])
def test_generate_mechanics() -> None:
    """Validate procedural room generation structure and probabilities."""
    # Test generation and make sure we get the expected types and structure.
    with patch("random.random", return_value=0.1):  # force items and enemies to spawn
        mechanics = generate_mechanics(floor=1)

        assert mechanics["room_type"] == {"name": "Cave", "description": "Dark"}
        assert len(mechanics["enemies"]) == 1
        assert mechanics["enemies"][0]["name"] == "Goblin"
        assert len(mechanics["npcs"]) == 0
        assert len(mechanics["items"]) == 1
        assert mechanics["items"][0]["name"] == "Health Potion"
        assert mechanics["items"][0]["effect_type"] == "healing"

    with patch("random.random", return_value=0.1):  # force npcs to spawn
        with patch("game.mechanics.ENEMIES", []):  # disable enemies so NPC can spawn
            mechanics = generate_mechanics(floor=1)
            assert len(mechanics["enemies"]) == 0
            assert len(mechanics["npcs"]) == 1
            assert mechanics["npcs"][0]["name"] == "Merchant"

    with patch("random.random", return_value=0.9):  # force nothing to spawn
        mechanics = generate_mechanics(floor=1)
        assert len(mechanics["enemies"]) == 0
        assert len(mechanics["npcs"]) == 0
        assert len(mechanics["items"]) == 0


@patch("game.mechanics.ENEMIES", [])
@patch("game.mechanics.NPCS", [])
@patch("game.mechanics.ITEMS", [{"name": "Iron Sword", "description": "Sharp"}])
@patch("game.mechanics.ROOMS", [])
def test_generate_mechanics_weapons() -> None:
    """Ensure weapons generated procedurally have valid weapon effects."""
    with patch("random.random", return_value=0.1):  # item will spawn
        mechanics = generate_mechanics(floor=2)
        assert len(mechanics["items"]) == 1
        assert mechanics["items"][0]["effect_type"] == "weapon"
        assert mechanics["items"][0]["stat_effect"] > 0


@patch("game.mechanics.ENEMIES", [])
@patch("game.mechanics.NPCS", [])
@patch("game.mechanics.ITEMS", [{"name": "Random Junk", "description": "Junk"}])
@patch("game.mechanics.ROOMS", [])
def test_generate_mechanics_junk() -> None:
    """Verify random flavor items lack mechanical combat properties."""
    with patch("random.random", return_value=0.1):  # item will spawn
        mechanics = generate_mechanics(floor=2)
        assert len(mechanics["items"]) == 1
        assert mechanics["items"][0]["effect_type"] == "none"
        assert mechanics["items"][0]["stat_effect"] == 0


def test_load_data_with_content_dir(tmp_path: Path) -> None:
    """Verify load_data reads from content_dir when the file exists there."""
    alt_file = tmp_path / "enemies.md"
    alt_file.write_text("- Space Pirate: Flies a stolen ship\n")

    result = load_data("enemies.md", content_dir=tmp_path)
    assert result == [{"name": "Space Pirate", "description": "Flies a stolen ship"}]


def test_load_data_content_dir_fallback(tmp_path: Path) -> None:
    """Verify load_data falls back to built-in data when file is absent in dir."""
    # tmp_path is empty – no enemies.md inside it
    result = load_data("enemies.md", content_dir=tmp_path)
    # The built-in enemies list must be non-empty
    assert len(result) > 0


def test_generate_mechanics_with_content_dir(tmp_path: Path) -> None:
    """Verify generate_mechanics uses data files from the content_dir."""
    (tmp_path / "enemies.md").write_text("- Robot: Beeps and boops\n")
    (tmp_path / "items.md").write_text("- Laser Sword: Cuts steel\n")
    (tmp_path / "npcs.md").write_text("- Android: Speaks binary\n")
    (tmp_path / "rooms.md").write_text("- Space Station: Zero-gravity corridors\n")

    with patch("random.random", return_value=0.1):  # force everything to spawn
        mechanics = generate_mechanics(floor=1, content_dir=tmp_path)

    assert mechanics["room_type"]["name"] == "Space Station"
    assert mechanics["enemies"][0]["name"] == "Robot"
    assert mechanics["items"][0]["name"] == "Laser Sword"


def test_generate_mechanics_content_dir_partial_override(tmp_path: Path) -> None:
    """Verify generate_mechanics falls back to built-in data for absent files."""
    # Only provide rooms.md; others absent → built-in data used
    (tmp_path / "rooms.md").write_text("- Moon Base: Dusty corridors\n")

    with patch("random.random", return_value=0.9):  # nothing spawns
        mechanics = generate_mechanics(floor=1, content_dir=tmp_path)

    assert mechanics["room_type"]["name"] == "Moon Base"
