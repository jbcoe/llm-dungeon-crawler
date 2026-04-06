"""Data models for game entities using Pydantic."""

from pydantic import BaseModel, ValidationInfo, field_validator


class Item(BaseModel):
    """Represents an item in the game."""

    name: str
    description: str
    stat_effect: int | None = 0
    effect_type: str | None = "none"  # healing, damage, none

    @field_validator("stat_effect", "effect_type", mode="before")
    @classmethod
    def set_defaults(cls, v: int | str | None, info: ValidationInfo) -> int | str:
        """Set default values for optional fields."""
        if v is None:
            return 0 if info.field_name == "stat_effect" else "none"
        return v


class Enemy(BaseModel):
    """Represents an enemy character."""

    name: str
    description: str
    hp: int | None = 10
    max_hp: int | None = 10
    attack: int | None = 5

    @field_validator("hp", "max_hp", "attack", mode="before")
    @classmethod
    def set_enemy_defaults(cls, v: int | None, info: ValidationInfo) -> int:
        """Set default values for enemy stats."""
        if v is None:
            return 5 if info.field_name == "attack" else 10
        return v


class NPC(BaseModel):
    """Represents a non-player character."""

    name: str
    description: str
    dialogue_context: str | None = ""


class Room(BaseModel):
    """Represents a room in the dungeon."""

    description: str
    exits: list[str]
    items: list[Item] = []
    enemies: list[Enemy] = []
    npcs: list[NPC] = []


class Player(BaseModel):
    """Represents the player character and their state."""

    hp: int = 100
    max_hp: int = 100
    attack: int = 10
    inventory: list[Item] = []
    equipped_weapon: Item | None = None

    @property
    def total_attack(self) -> int:
        """Calculate total attack including weapon bonuses."""
        bonus = (
            self.equipped_weapon.stat_effect
            if self.equipped_weapon and self.equipped_weapon.stat_effect
            else 0
        )
        return self.attack + bonus

    def take_damage(self, amount: int) -> None:
        """Reduce player HP by the specified amount."""
        self.hp = max(0, self.hp - amount)

    def heal(self, amount: int) -> None:
        """Increase player HP by the specified amount, up to max HP."""
        self.hp = min(self.max_hp, self.hp + amount)
