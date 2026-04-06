from pydantic import BaseModel, field_validator


class Item(BaseModel):
    name: str
    description: str
    stat_effect: int | None = 0
    effect_type: str | None = "none"  # healing, damage, none

    @field_validator("stat_effect", "effect_type", mode="before")
    @classmethod
    def set_defaults(cls, v, info):
        if v is None:
            return 0 if info.field_name == "stat_effect" else "none"
        return v


class Enemy(BaseModel):
    name: str
    description: str
    hp: int | None = 10
    max_hp: int | None = 10
    attack: int | None = 5

    @field_validator("hp", "max_hp", "attack", mode="before")
    @classmethod
    def set_enemy_defaults(cls, v, info):
        if v is None:
            return 5 if info.field_name == "attack" else 10
        return v


class NPC(BaseModel):
    name: str
    description: str
    dialogue_context: str | None = ""


class Room(BaseModel):
    description: str
    exits: list[str]
    items: list[Item] = []
    enemies: list[Enemy] = []
    npcs: list[NPC] = []


class Player(BaseModel):
    hp: int = 100
    max_hp: int = 100
    attack: int = 10
    inventory: list[Item] = []
    equipped_weapon: Item | None = None

    @property
    def total_attack(self) -> int:
        bonus = (
            self.equipped_weapon.stat_effect
            if self.equipped_weapon and self.equipped_weapon.stat_effect
            else 0
        )
        return self.attack + bonus

    def take_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)
