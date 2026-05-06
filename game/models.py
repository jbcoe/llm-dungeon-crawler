"""Data models for game entities using Pydantic."""

from pydantic import BaseModel, ConfigDict, Field


class GameModel(BaseModel):
    """Base model for all game entities."""

    model_config = ConfigDict(strict=True)


class Item(GameModel):
    """Represents an item in the game."""

    name: str
    description: str
    stat_effect: int = Field(default=0)
    effect_type: str = Field(default="none")  # healing, weapon, none


class Enemy(GameModel):
    """Represents an enemy character."""

    name: str
    description: str
    hp: int = Field(default=10)
    max_hp: int = Field(default=10)
    attack: int = Field(default=5)
    is_boss: bool = Field(default=False)


class NPC(GameModel):
    """Represents a non-player character."""

    name: str
    description: str
    dialogue_context: str = Field(default="")


class Room(GameModel):
    """Represents a room in the dungeon."""

    name: str
    description: str
    exits: list[str] = Field(default_factory=list)
    items: list[Item] = Field(default_factory=list)
    enemies: list[Enemy] = Field(default_factory=list)
    npcs: list[NPC] = Field(default_factory=list)
    is_final_room: bool = Field(default=False)


class Player(GameModel):
    """Represents the player character and their state."""

    hp: int = Field(default=100)
    max_hp: int = Field(default=100)
    attack: int = Field(default=10)
    inventory: list[Item] = Field(default_factory=list)
    equipped_weapon: Item | None = Field(default=None)

    @property
    def total_attack(self) -> int:
        """Calculate total attack including weapon bonuses."""
        bonus = self.equipped_weapon.stat_effect if self.equipped_weapon else 0
        return self.attack + bonus

    def take_damage(self, amount: int) -> None:
        """Reduce player HP by the specified amount."""
        self.hp = max(0, self.hp - amount)

    def heal(self, amount: int) -> None:
        """Increase player HP by the specified amount, up to max HP."""
        self.hp = min(self.max_hp, self.hp + amount)
