"""Data models for game entities using Pydantic."""

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class Item(BaseModel):
    """Represents an item in the game."""

    name: str
    description: str
    stat_effect: int = Field(default=0)
    effect_type: str = Field(default="none")  # healing, damage, none, weapon

    @field_validator("stat_effect", "effect_type", mode="before")
    @classmethod
    def set_defaults(cls, v: int | str | None, info: ValidationInfo) -> int | str:
        """Set default values for optional fields if None is passed."""
        if v is None:
            return 0 if info.field_name == "stat_effect" else "none"
        return v


class Enemy(BaseModel):
    """Represents an enemy character."""

    name: str
    description: str
    hp: int = Field(default=10)
    max_hp: int = Field(default=10)
    attack: int = Field(default=5)

    @field_validator("hp", "max_hp", "attack", mode="before")
    @classmethod
    def set_enemy_defaults(cls, v: int | None, info: ValidationInfo) -> int:
        """Set default values for enemy stats if None is passed."""
        if v is None:
            return 5 if info.field_name == "attack" else 10
        return v


class NPC(BaseModel):
    """Represents a non-player character."""

    name: str
    description: str
    dialogue_context: str = Field(default="")


class Room(BaseModel):
    """Represents a room in the dungeon."""

    description: str
    exits: list[str] = Field(default_factory=list)
    items: list[Item] = Field(default_factory=list)
    enemies: list[Enemy] = Field(default_factory=list)
    npcs: list[NPC] = Field(default_factory=list)


class Player(BaseModel):
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
