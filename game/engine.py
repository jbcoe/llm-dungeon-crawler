"""Core game engine responsible for the game loop and command handling."""

import random

from pydantic import BaseModel, Field
from rich.console import Console
from rich.markup import escape

from game.ai import AIGenerator
from game.logger import log_event, setup_logger
from game.map import Map
from game.mechanics import ENEMIES
from game.models import Enemy, Player, Room


class CommandInfo(BaseModel):
    """Type definition for a command in the engine."""

    usage: str
    desc: str
    aliases: list[str] = Field(default_factory=list)


COMMANDS: dict[str, CommandInfo] = {
    "look": CommandInfo(usage="look", desc="Describe the current room again"),
    "go": CommandInfo(
        usage="go <dir>",
        desc="Move in a direction (north, south, east, west)",
    ),
    "attack": CommandInfo(
        usage="attack <enemy>",
        desc="Attack an enemy in the room",
    ),
    "talk": CommandInfo(
        usage="talk <npc>",
        desc="Start a conversation with an NPC",
    ),
    "take": CommandInfo(usage="take <item>", desc="Pick up an item"),
    "use": CommandInfo(
        usage="use <item>",
        desc="Use an item from your inventory",
    ),
    "equip": CommandInfo(
        usage="equip <weapon>",
        desc="Equip a weapon from your inventory",
    ),
    "unequip": CommandInfo(
        usage="unequip",
        desc="Unequip your current weapon",
    ),
    "status": CommandInfo(
        usage="status",
        desc="Check your HP and inventory",
        aliases=["inventory", "i", "stats", "me"],
    ),
    "help": CommandInfo(usage="help", desc="Show this help message"),
    "quit": CommandInfo(usage="quit", desc="Exit the game", aliases=["exit"]),
    "rest": CommandInfo(
        usage="rest",
        desc="Rest awhile to recover HP (enemies may appear)",
    ),
    "map": CommandInfo(
        usage="map",
        desc="Show a map of explored rooms",
    ),
}

# Enemy spawn probability when resting: starts at 20%, increases by 15% per
# consecutive rest in the same room, capped at 95%.
_REST_BASE_SPAWN_CHANCE = 0.20
_REST_SPAWN_INCREMENT = 0.15


class GameUI:
    """Handles all user interface interactions using Rich."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the GameUI."""
        self.console = console or Console()

    def print(self, message: str, style: str = "", markup: bool = True) -> None:
        """Print a message to the console with an optional style."""
        if style:
            self.console.print(message, style=style, markup=markup)
        else:
            self.console.print(message, markup=markup)

    def print_italic(self, message: str) -> None:
        """Print a message in italic style."""
        self.print(message, style="italic", markup=False)

    def print_error(self, message: str) -> None:
        """Print an error message in red."""
        self.print(message, style="red", markup=False)

    def display_room(self, room: Room) -> None:
        """Print the description and contents of the current room."""
        self.print(f"\n[bold cyan]Room: {escape(room.name)}[/bold cyan]")
        self.print(f"{escape(room.description)}")
        self.print(f"[bold yellow]Exits:[/bold yellow] {', '.join(room.exits)}")

        if room.items:
            for item in room.items:
                self.print(
                    f"[bold green]Loot:[/bold green] {escape(item.name)} "
                    f"- {escape(item.description)}"
                )

        if room.enemies:
            for enemy in room.enemies:
                self.print(
                    f"[bold red]Enemy:[/bold red] {escape(enemy.name)} "
                    f"(HP: {enemy.hp}/{enemy.max_hp}) - {escape(enemy.description)}"
                )

        if room.npcs:
            for npc in room.npcs:
                self.print(
                    f"[bold blue]NPC:[/bold blue] {escape(npc.name)} "
                    f"- {escape(npc.description)}"
                )

    def display_status(self, player: Player) -> None:
        """Display player health, attack stats, and inventory."""
        self.print(f"[bold magenta]HP:[/bold magenta] {player.hp}/{player.max_hp}")
        weapon_name = player.equipped_weapon.name if player.equipped_weapon else "None"
        self.print(
            f"[bold magenta]Attack:[/bold magenta] {player.total_attack} "
            f"(Base: {player.attack}, Weapon: {weapon_name})"
        )
        inventory = ", ".join([i.name for i in player.inventory]) or "Empty"
        self.print(f"[bold magenta]Inventory:[/bold magenta] {inventory}")

    def display_map(
        self,
        map_grid: Map,
        current_pos: tuple[int, int],
        explored: set[tuple[int, int]],
    ) -> None:
        """Display an ASCII art map of the dungeon."""
        self.print("\n[bold yellow]Dungeon Map:[/bold yellow]")

        # Directions: NORTH is (0, 1), so top row is max y
        for y in range(map_grid.size - 1, -1, -1):
            row: list[str] = []
            for x in range(map_grid.size):
                coord = (x, y)
                if coord == current_pos:
                    row.append("[bold red]*[/bold red]")
                elif coord in explored:
                    row.append("[bold green]o[/bold green]")
                elif map_grid.space[x, y]:
                    # Check if it's an unexplored exit (adjacent to explored)
                    is_unexplored_exit = False
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        if (x + dx, y + dy) in explored:
                            is_unexplored_exit = True
                            break
                    if is_unexplored_exit:
                        row.append("[white]?[/white]")
                    else:
                        row.append(" ")
                else:
                    row.append(" ")
            self.print(" ".join(row))


class GameEngine:
    """Main game engine class managing state and logic."""

    def __init__(
        self,
        mock_input: list[str] | None = None,
        max_history: int = 1000,
        model: str = "gemma4:e4b",
        ai_generator: AIGenerator | None = None,
        map_size: int = 8,
        map_seed: int | None = None,
    ) -> None:
        """Initialize the game engine."""
        self.player = Player()
        self.ai = ai_generator or AIGenerator(model=model)
        self.model = self.ai.model
        self.floor = 1
        self.current_room: Room | None = None
        self.running = True
        self.history: list[str] = []
        self.max_history = max_history
        self.mock_input = mock_input
        self.map_grid = Map(size=map_size, seed=map_seed)
        self.x = 1
        self.y = 1
        self.grid: dict[tuple[int, int], Room] = {}
        self.ui = GameUI()
        self.rest_count = 0
        self.setup_readline()

    def setup_readline(self) -> None:
        """Configure readline for command completion and history."""
        if self.mock_input is not None:
            return
        try:
            import readline
            import sys

            if (
                sys.platform == "darwin"
                and readline.__doc__
                and "libedit" in readline.__doc__
            ):
                readline.parse_and_bind("bind ^I rl_complete")
            else:
                readline.parse_and_bind("tab: complete")

            readline.set_history_length(self.max_history)

            def completer(text: str, state: int) -> str | None:
                options = self.get_completion_options()
                matches = [
                    opt for opt in options if opt.lower().startswith(text.lower())
                ]
                if state < len(matches):
                    return matches[state]
                return None

            readline.set_completer(completer)
        except ImportError:
            pass

    def display_room(self) -> None:
        """Backward compatibility helper to display the current room."""
        if self.current_room:
            self.ui.display_room(self.current_room)

    def display_status(self) -> None:
        """Backward compatibility helper to display player status."""
        self.ui.display_status(self.player)

    def get_completion_options(self) -> list[str]:
        """Generate a list of available words for autocompletion."""
        options = []
        for cmd, info in COMMANDS.items():
            options.append(cmd)
            options.extend(info.aliases)

        if self.current_room:
            options.extend(self.current_room.exits)
            for e in self.current_room.enemies:
                options.extend(e.name.lower().split())
            for n in self.current_room.npcs:
                options.extend(n.name.lower().split())
            for item in self.current_room.items:
                options.extend(item.name.lower().split())
        for item in self.player.inventory:
            options.extend(item.name.lower().split())

        return sorted(list(set(options)))

    def get_input(self, prompt: str) -> str:
        """Get input from the user or mock input if provided."""
        if self.mock_input is not None:
            if self.mock_input:
                return self.mock_input.pop(0)
            return "quit"
        return input(prompt)

    def start(self) -> None:
        """Start the game session."""
        if self.mock_input is None:
            setup_logger()
        log_event("GAME_START", "Starting new game session.")
        self.ui.print("Welcome to the AI Dungeon Crawler!", style="bold green")
        intro_text = self.ai.generate_intro()
        self.ui.print_italic(f"\n{intro_text}\n")
        self.enter_new_room("start")
        self.game_loop()

    def enter_new_room(self, direction: str) -> None:
        """Handle moving into a new or existing room."""
        self.rest_count = 0
        if direction == "north":
            self.y += 1
        elif direction == "south":
            self.y -= 1
        elif direction == "east":
            self.x += 1
        elif direction == "west":
            self.x -= 1

        coord = (self.x, self.y)
        if direction != "start":
            self.ui.print_italic(f"You travel {direction}...")

        if coord in self.grid:
            self.ui.print_italic("You've been here before.")
            self.current_room = self.grid[coord]
        else:
            context = (
                " ".join(self.history[-3:])
                if self.history
                else "Beginning of the journey."
            )
            map_exits: list[str] = []
            try:
                map_exits = self.map_grid.get_exits(self.x, self.y)
                room_data = self.ai.generate_room(self.floor, context, exits=map_exits)
                self.current_room = Room(**room_data)
                self.grid[coord] = self.current_room
            except Exception as e:
                log_event("ERROR: room_generation", str(e))
                # Fallback room
                self.current_room = Room(
                    name="Stone Chamber",
                    description="A non-descript stone chamber.",
                    exits=map_exits or ["north"],
                )
                self.grid[coord] = self.current_room

        if self.current_room:
            self.ui.display_room(self.current_room)

    def game_loop(self) -> None:
        """Run the main input-process-output loop."""
        while self.running and self.player.hp > 0:
            self.ui.print("")
            command_line = self.get_input("> ").strip()
            if not command_line:
                continue

            log_event("PLAYER_ACTION", f"> {command_line}")
            self.history.append(command_line)
            if len(self.history) > self.max_history:
                self.history.pop(0)

            parts = command_line.lower().split()
            action = parts[0]

            if action in ["quit", "exit"] and len(parts) == 1:
                self.running = False
                self.ui.print("Thanks for playing!")
            elif action == "help":
                self.handle_help()
            elif action == "look":
                if self.current_room:
                    self.ui.display_room(self.current_room)
            elif action == "map":
                self.handle_map()
            elif action in ["status", "inventory", "i", "stats", "me"]:
                self.ui.display_status(self.player)
            elif action == "go":
                self.handle_go(parts)
            elif action == "attack":
                self.handle_attack(parts)
            elif action == "talk":
                self.handle_talk(parts)
            elif action == "take":
                self.handle_take(parts)
            elif action == "use":
                self.handle_use(parts)
            elif action == "equip":
                self.handle_equip(parts)
            elif action == "unequip":
                self.handle_unequip()
            elif action == "rest":
                self.handle_rest()
            else:
                self.ui.print("Unknown command. Type 'help'.")

        if self.player.hp <= 0:
            log_event("GAME_END", "Game Over. Player died.")
            self.ui.print("Game Over. You have died.", style="bold red")

    def handle_help(self) -> None:
        """Handle the help command."""
        self.ui.print("\n[bold]Available Commands:[/bold]")
        for info in COMMANDS.values():
            self.ui.print(f"  {info.usage.ljust(15)} - {info.desc}")

    def handle_map(self) -> None:
        """Handle the map command."""
        self.ui.display_map(self.map_grid, (self.x, self.y), set(self.grid.keys()))

    def handle_go(self, parts: list[str]) -> None:
        """Handle the go command."""
        if not self.current_room:
            return

        if len(parts) > 1:
            direction = parts[1]
            if direction in self.current_room.exits:
                if self.current_room.enemies:
                    self.ui.print_error("You can't leave while there are enemies here!")
                else:
                    self.enter_new_room(direction)
                    self.floor += 1
            else:
                self.ui.print(f"You cannot go '{direction}'.")
        else:
            self.ui.print("Go where?")

    @staticmethod
    def _roll_damage(base: int) -> int:
        """Return 0 if base <= 0, else randomized damage in [75%, 125%] of base."""
        if base <= 0:
            return 0
        lo = max(1, base * 75 // 100)
        hi = max(1, base * 125 // 100)
        return random.randint(lo, hi)

    def handle_attack(self, parts: list[str]) -> None:
        """Handle the attack command."""
        if not self.current_room or not self.current_room.enemies:
            self.ui.print("There is nothing to attack here.")
            return

        target_name = (
            " ".join(parts[1:]) if len(parts) > 1 else self.current_room.enemies[0].name
        )

        enemy = next(
            (
                e
                for e in self.current_room.enemies
                if e.name.lower() == target_name.lower()
            ),
            None,
        )
        if not enemy:
            enemy = next(
                (
                    e
                    for e in self.current_room.enemies
                    if target_name.lower() in e.name.lower()
                ),
                None,
            )

        if not enemy:
            self.ui.print(f"No enemy named '{target_name}' here.")
            return

        # Player attacks with randomized damage
        damage = self._roll_damage(self.player.total_attack)
        enemy.hp -= damage
        self.ui.print(f"You attack {enemy.name} for {damage} damage!")

        # Enemy attacks if still alive, also with randomized damage
        if enemy.hp > 0:
            enemy_damage = self._roll_damage(enemy.attack)
            self.player.take_damage(enemy_damage)
            self.ui.print(f"{enemy.name} attacks you for {enemy_damage} damage!")
        else:
            self.ui.print(f"You defeated {enemy.name}!", style="bold red")
            self.current_room.enemies.remove(enemy)

        # Narrative
        narrative = self.ai.narrate_combat(
            player_action="attacked with a weapon",
            player_hp=self.player.hp,
            enemy_name=enemy.name,
            enemy_hp=max(0, enemy.hp),
            damage_dealt=damage,
        )
        self.ui.print_italic(narrative)

    def handle_talk(self, parts: list[str]) -> None:
        """Handle the talk command."""
        if not self.current_room or not self.current_room.npcs:
            self.ui.print("There is no one here to talk to.")
            return

        if len(parts) == 1:
            self.ui.print("Talk to whom?")
            return

        target_name = " ".join(parts[1:])
        npc = next(
            (
                n
                for n in self.current_room.npcs
                if n.name.lower() == target_name.lower()
            ),
            None,
        )
        if not npc:
            npc = next(
                (
                    n
                    for n in self.current_room.npcs
                    if target_name.lower() in n.name.lower()
                ),
                None,
            )

        if not npc:
            self.ui.print(f"No one named '{target_name}' here.")
            return

        self.ui.print(
            f"You approach {npc.name}. (Type 'bye' or 'leave' to end conversation)",
            style="bold blue",
        )

        history = ""
        while True:
            player_msg = self.get_input("You: ").strip()
            if not player_msg:
                continue

            if player_msg.lower() in ["bye", "leave", "quit", "exit"]:
                self.ui.print(f"{npc.name} nods as you walk away.", style="bold blue")
                break

            response = self.ai.generate_npc_response(
                npc.name, npc.dialogue_context, player_msg, history
            )
            self.ui.print(f"{npc.name}: {response}", style="bold blue")

            history += f"\nPlayer: {player_msg}\nNPC: {response}"
            if len(history) > 1000:
                history = history[-1000:]

    def handle_take(self, parts: list[str]) -> None:
        """Handle the take command."""
        if not self.current_room:
            return

        if len(parts) > 1:
            item_name = " ".join(parts[1:])
            item = next(
                (
                    i
                    for i in self.current_room.items
                    if i.name.lower() == item_name.lower()
                ),
                None,
            )
            if not item:
                item = next(
                    (
                        i
                        for i in self.current_room.items
                        if item_name.lower() in i.name.lower()
                    ),
                    None,
                )

            if item:
                self.player.inventory.append(item)
                self.current_room.items.remove(item)
                self.ui.print(f"You took the {item.name}.")
            else:
                self.ui.print(f"No item named '{item_name}' here.")
        else:
            self.ui.print("Take what?")

    def handle_use(self, parts: list[str]) -> None:
        """Handle the use command."""
        if len(parts) > 1:
            item_name = " ".join(parts[1:])
            item = next(
                (
                    i
                    for i in self.player.inventory
                    if i.name.lower() == item_name.lower()
                ),
                None,
            )
            if not item:
                item = next(
                    (
                        i
                        for i in self.player.inventory
                        if item_name.lower() in i.name.lower()
                    ),
                    None,
                )

            if item:
                if item.effect_type == "healing":
                    self.player.heal(item.stat_effect)
                    self.ui.print(
                        f"You used {item.name} and healed {item.stat_effect} HP."
                    )
                    self.player.inventory.remove(item)
                elif item.effect_type == "weapon":
                    self.ui.print(f"To use {item.name}, you must 'equip' it.")
                else:
                    room_desc = (
                        self.current_room.description
                        if self.current_room
                        else "Unknown"
                    )
                    narration = self.ai.narrate_item_use(
                        item.name, item.description, room_desc
                    )
                    self.ui.print_italic(narration)
            else:
                self.ui.print(f"You don't have an item named '{item_name}'.")
        else:
            self.ui.print("Use what?")

    def handle_equip(self, parts: list[str]) -> None:
        """Handle the equip command."""
        if len(parts) > 1:
            item_name = " ".join(parts[1:])
            item = next(
                (
                    i
                    for i in self.player.inventory
                    if i.name.lower() == item_name.lower()
                ),
                None,
            )
            if not item:
                item = next(
                    (
                        i
                        for i in self.player.inventory
                        if item_name.lower() in i.name.lower()
                    ),
                    None,
                )

            if item:
                if item.effect_type == "weapon":
                    if self.player.equipped_weapon:
                        self.player.inventory.append(self.player.equipped_weapon)
                        self.ui.print(
                            f"You unequipped {self.player.equipped_weapon.name}."
                        )

                    self.player.equipped_weapon = item
                    self.player.inventory.remove(item)
                    self.ui.print(
                        f"You equipped {item.name}! Your attack is now "
                        f"{self.player.total_attack}.",
                        style="bold cyan",
                    )
                else:
                    self.ui.print(f"You can't equip {item.name}. It's not a weapon.")
            else:
                self.ui.print(f"You don't have an item named '{item_name}'.")
        else:
            self.ui.print("Equip what?")

    def handle_unequip(self) -> None:
        """Handle the unequip command."""
        if self.player.equipped_weapon:
            item = self.player.equipped_weapon
            self.player.inventory.append(item)
            self.player.equipped_weapon = None
            self.ui.print(
                f"You unequipped {item.name}. Your attack is now "
                f"{self.player.total_attack}.",
                style="bold cyan",
            )
        else:
            self.ui.print("You don't have a weapon equipped.")

    def handle_rest(self) -> None:
        """Handle the rest command - player rests, risking enemy spawns."""
        if not self.current_room:
            return

        if self.current_room.enemies:
            self.ui.print_error("You can't rest while enemies are present!")
            return

        # Recover a portion of max HP (20%, minimum 5)
        heal_amount = max(5, self.player.max_hp // 5)
        hp_before = self.player.hp
        self.player.heal(heal_amount)
        actual_healed = self.player.hp - hp_before

        self.ui.print(
            f"You rest awhile and recover {actual_healed} HP. "
            f"HP: {self.player.hp}/{self.player.max_hp}"
        )

        narrative = self.ai.narrate_rest(self.player.hp, self.player.max_hp)
        self.ui.print_italic(narrative)

        # Enemy spawn probability increases with each consecutive rest in the same room
        # First rest: 20%, second: 35%, third: 50%, etc., capped at 95%
        spawn_chance = min(
            _REST_BASE_SPAWN_CHANCE + self.rest_count * _REST_SPAWN_INCREMENT, 0.95
        )
        self.rest_count += 1

        if ENEMIES and random.random() < spawn_chance:
            enemy_data = random.choice(ENEMIES)
            hp = 10 + self.floor * 5
            attack = 3 + self.floor * 2
            new_enemy = Enemy(
                name=enemy_data["name"],
                description=enemy_data["description"],
                hp=hp,
                max_hp=hp,
                attack=attack,
            )
            self.current_room.enemies.append(new_enemy)
            self.ui.print(
                f"[bold red]A {new_enemy.name} appears while you rested![/bold red]"
            )
            self.rest_count = 0
