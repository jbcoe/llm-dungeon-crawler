"""Unit tests for mechanics.py."""

from unittest.mock import patch

from game.mechanics import generate_final_room_mechanics, generate_mechanics, load_data


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


# ---------------------------------------------------------------------------
# generate_final_room_mechanics
# ---------------------------------------------------------------------------


@patch(
    "game.mechanics.BOSSES",
    [{"name": "Test Boss", "description": "A terrible foe"}],
)
@patch("game.mechanics.ITEMS", [{"name": "Healing Potion", "description": "Heals HP"}])
def test_generate_final_room_mechanics_structure() -> None:
    """Verify the final room mechanics dict has the expected shape."""
    mechanics = generate_final_room_mechanics(floor=3, exits=["south"])

    assert mechanics["is_final_room"] is True
    assert mechanics["exits"] == ["south"]
    assert mechanics["npcs"] == []

    # Exactly one boss enemy
    assert len(mechanics["enemies"]) == 1
    boss = mechanics["enemies"][0]
    assert boss["name"] == "Test Boss"
    assert boss["is_boss"] is True
    assert boss["hp"] > 0
    assert boss["attack"] > 0

    # At least one guaranteed item
    assert len(mechanics["items"]) >= 1

    # Room type is one of the special final room types
    assert "name" in mechanics["room_type"]
    assert "description" in mechanics["room_type"]


@patch(
    "game.mechanics.BOSSES",
    [{"name": "Test Boss", "description": "A terrible foe"}],
)
@patch("game.mechanics.ITEMS", [{"name": "Healing Potion", "description": "Heals HP"}])
def test_generate_final_room_mechanics_scales_with_floor() -> None:
    """Boss stats should be higher on deeper floors."""
    mechanics_low = generate_final_room_mechanics(floor=1)
    mechanics_high = generate_final_room_mechanics(floor=10)

    boss_low = mechanics_low["enemies"][0]
    boss_high = mechanics_high["enemies"][0]

    assert boss_high["hp"] > boss_low["hp"]
    assert boss_high["attack"] > boss_low["attack"]


@patch("game.mechanics.BOSSES", [])
@patch("game.mechanics.ITEMS", [])
def test_generate_final_room_mechanics_fallback_boss() -> None:
    """A fallback Dark Lord boss is used when BOSSES list is empty."""
    mechanics = generate_final_room_mechanics(floor=1)

    boss = mechanics["enemies"][0]
    assert boss["name"] == "The Dark Lord"
    assert boss["is_boss"] is True


def test_bosses_data_loaded() -> None:
    """Verify that bosses.md is loaded and contains usable boss entries."""
    from game.mechanics import BOSSES

    assert len(BOSSES) > 0
    for boss in BOSSES:
        assert "name" in boss
        assert "description" in boss
        assert boss["name"]
        assert boss["description"]
