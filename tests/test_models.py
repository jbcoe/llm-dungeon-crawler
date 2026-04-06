"""Unit tests for Pydantic models in game/models.py."""

from game.models import Enemy, Item, Player


def test_item_defaults() -> None:
    """Ensure Item initializes default fields and handles None values."""
    item = Item(name="Test", description="Desc")
    assert item.stat_effect == 0
    assert item.effect_type == "none"

    item2 = Item(name="Test2", description="Desc", stat_effect=None, effect_type=None)
    assert item2.stat_effect == 0
    assert item2.effect_type == "none"

    item3 = Item(name="Test3", description="Desc", stat_effect=10, effect_type="damage")
    assert item3.stat_effect == 10
    assert item3.effect_type == "damage"


def test_enemy_defaults() -> None:
    """Verify Enemy stats correctly default if omitted or None."""
    enemy = Enemy(name="Test", description="Desc")
    assert enemy.hp == 10
    assert enemy.max_hp == 10
    assert enemy.attack == 5

    enemy2 = Enemy(name="Test2", description="Desc", hp=None, max_hp=None, attack=None)
    assert enemy2.hp == 10
    assert enemy2.max_hp == 10
    assert enemy2.attack == 5

    enemy3 = Enemy(name="Test3", description="Desc", hp=20, max_hp=30, attack=15)
    assert enemy3.hp == 20
    assert enemy3.max_hp == 30
    assert enemy3.attack == 15


def test_player_attack_no_weapon() -> None:
    """Check that base attack returns correctly without equipment bonuses."""
    player = Player(attack=10)
    assert player.total_attack == 10


def test_player_attack_with_weapon() -> None:
    """Validate that equipping a weapon computes total_attack correctly."""
    weapon = Item(
        name="Sword", description="Sharp", effect_type="weapon", stat_effect=5
    )
    player = Player(attack=10, equipped_weapon=weapon)
    assert player.total_attack == 15


def test_player_take_damage() -> None:
    """Ensure player takes damage and does not fall below zero HP."""
    player = Player(hp=100)
    player.take_damage(20)
    assert player.hp == 80

    player.take_damage(100)
    assert player.hp == 0  # Should not go below 0


def test_player_heal() -> None:
    """Verify that healing logic does not push player HP over max_hp bounds."""
    player = Player(hp=50, max_hp=100)
    player.heal(30)
    assert player.hp == 80

    player.heal(50)
    assert player.hp == 100  # Should not exceed max_hp
