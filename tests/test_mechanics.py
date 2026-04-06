"""Unit tests for mechanics.py."""

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
