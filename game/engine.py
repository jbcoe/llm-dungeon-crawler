"""Core game engine responsible for the game loop and command handling."""

from game.models import Player, Room
from game.ai import (
    generate_room,
    narrate_combat,
    generate_npc_response,
    generate_intro,
    narrate_item_use,
)
from game.logger import setup_logger, log_event
from rich.console import Console

COMMANDS = {
    "look": {"usage": "look", "desc": "Describe the current room again", "aliases": []},
    "go": {
        "usage": "go <dir>",
        "desc": "Move in a direction (north, south, etc.)",
        "aliases": [],
    },
    "attack": {
        "usage": "attack <enemy>",
        "desc": "Attack an enemy in the room",
        "aliases": [],
    },
    "talk": {
        "usage": "talk <npc>",
        "desc": "Start a conversation with an NPC",
        "aliases": [],
    },
    "take": {"usage": "take <item>", "desc": "Pick up an item", "aliases": []},
    "use": {
        "usage": "use <item>",
        "desc": "Use an item from your inventory",
        "aliases": [],
    },
    "equip": {
        "usage": "equip <weapon>",
        "desc": "Equip a weapon from your inventory",
        "aliases": [],
    },
    "unequip": {
        "usage": "unequip",
        "desc": "Unequip your current weapon",
        "aliases": [],
    },
    "status": {
        "usage": "status",
        "desc": "Check your HP and inventory",
        "aliases": ["inventory", "i", "stats", "me"],
    },
    "help": {"usage": "help", "desc": "Show this help message", "aliases": []},
    "quit": {"usage": "quit", "desc": "Exit the game", "aliases": ["exit"]},
}

ALL_COMMAND_WORDS = []
for cmd, info in COMMANDS.items():
    ALL_COMMAND_WORDS.append(cmd)
    ALL_COMMAND_WORDS.extend(info["aliases"])

console = Console()


class GameEngine:
    """Main game engine class managing state and logic."""

    def __init__(self, mock_input=None, max_history: int = 1000):
        """Initialize the game engine."""
        self.player = Player()
        self.floor = 1
        self.current_room = None
        self.running = True
        self.history = []
        self.max_history = max_history
        self.mock_input = mock_input  # For testing purposes
        self.x = 0
        self.y = 0
        self.grid = {}
        self.setup_readline()

    def setup_readline(self):
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

            def completer(text, state):
                options = self.get_completion_options()
                matches = [opt for opt in options if opt.startswith(text.lower())]
                if state < len(matches):
                    return matches[state]
                return None

            readline.set_completer(completer)
        except ImportError:
            pass

    def get_completion_options(self) -> list[str]:
        """Generate a list of available words for autocompletion."""
        options = list(ALL_COMMAND_WORDS)
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

    def start(self):
        """Start the game session."""
        if self.mock_input is None:
            setup_logger()
        log_event("GAME_START", "Starting new game session.")
        console.print("[bold green]Welcome to the AI Dungeon Crawler![/bold green]")
        intro_text = generate_intro()
        console.print(f"\n[italic]{intro_text}[/italic]\n")
        self.enter_new_room()
        self.game_loop()

    def enter_new_room(self, direction: str = "forward"):
        """Handle moving into a new or existing room."""
        if direction == "north":
            self.y += 1
        elif direction == "south":
            self.y -= 1
        elif direction == "east":
            self.x += 1
        elif direction == "west":
            self.x -= 1

        coord = (self.x, self.y)

        console.print(f"[italic]You travel {direction}...[/italic]")

        if coord in self.grid:
            console.print("[italic]You've been here before.[/italic]")
            self.current_room = self.grid[coord]
        else:
            context = " ".join(self.history[-3:])
            room_data = generate_room(self.floor, context)
            self.current_room = Room(**room_data)
            self.grid[coord] = self.current_room

        self.display_room()

    def display_room(self):
        """Print the description and contents of the current room."""
        if not self.current_room:
            return
        console.print(
            f"\n[bold cyan]Room Description:[/bold cyan] {self.current_room.description}"
        )
        console.print(
            f"[bold yellow]Exits:[/bold yellow] {', '.join(self.current_room.exits)}"
        )
        if self.current_room.items:
            for item in self.current_room.items:
                console.print(
                    f"[bold green]Loot:[/bold green] {item.name} - {item.description}"
                )
        if self.current_room.enemies:
            for enemy in self.current_room.enemies:
                console.print(
                    f"[bold red]Enemy:[/bold red] {enemy.name} (HP: {enemy.hp}/{enemy.max_hp}) - {enemy.description}"
                )
        if self.current_room.npcs:
            for npc in self.current_room.npcs:
                console.print(
                    f"[bold blue]NPC:[/bold blue] {npc.name} - {npc.description}"
                )

    def game_loop(self):
        """Run the main input-process-output loop."""
        while self.running and self.player.hp > 0:
            console.print("")
            command = self.get_input("> ").strip().lower()
            if not command:
                continue

            log_event("PLAYER_ACTION", f"> {command}")

            if self.max_history <= 0:
                self.history = []
            else:
                self.history.append(command)
                if len(self.history) > self.max_history:
                    self.history = self.history[-self.max_history :]
            parts = command.split()
            action = parts[0]

            if action in ["quit", "exit"] and len(parts) == 1:
                self.running = False
                console.print("Thanks for playing!")
                break
            elif action == "help":
                console.print("\n[bold]Available Commands:[/bold]", markup=True)
                for cmd, info in COMMANDS.items():
                    console.print(
                        f"  {info['usage'].ljust(15)} - {info['desc']}", markup=False
                    )
            elif action == "look":
                self.display_room()
            elif action in ["status", "inventory", "i", "stats", "me"]:
                self.display_status()
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
            else:
                console.print("Unknown command. Type 'help'.")

        if self.player.hp <= 0:
            log_event("GAME_END", "Game Over. Player died.")
            console.print("[bold red]Game Over. You have died.[/bold red]")

    def display_status(self):
        """Display player health, attack stats, and inventory."""
        console.print(
            f"[bold magenta]HP:[/bold magenta] {self.player.hp}/{self.player.max_hp}"
        )
        weapon_name = (
            self.player.equipped_weapon.name if self.player.equipped_weapon else "None"
        )
        console.print(
            f"[bold magenta]Attack:[/bold magenta] {self.player.total_attack} (Base: {self.player.attack}, Weapon: {weapon_name})"
        )
        inventory = ", ".join([i.name for i in self.player.inventory]) or "Empty"
        console.print(f"[bold magenta]Inventory:[/bold magenta] {inventory}")

    def handle_go(self, parts: list):
        """Process the 'go' command to move between rooms."""
        if not self.current_room:
            return

        if len(parts) > 1:
            direction = parts[1]
            if direction in self.current_room.exits:
                if self.current_room.enemies:
                    console.print(
                        "[red]You can't leave while there are enemies here![/red]"
                    )
                else:
                    self.enter_new_room(direction)
                    self.floor += 1
            else:
                console.print(f"You cannot go '{direction}'.")
        else:
            console.print("Go where?")

    def handle_attack(self, parts: list):
        """Process the 'attack' command to engage enemies."""
        if not self.current_room or not self.current_room.enemies:
            console.print("There is nothing to attack here.")
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
            # try partial match
            enemy = next(
                (
                    e
                    for e in self.current_room.enemies
                    if target_name.lower() in e.name.lower()
                ),
                None,
            )

        if not enemy:
            console.print(f"No enemy named '{target_name}' here.")
            return

        # Player attacks
        damage = self.player.total_attack
        enemy.hp -= damage
        console.print(f"You attack {enemy.name} for {damage} damage!")

        # Enemy attacks if still alive
        enemy_damage = 0
        if enemy.hp > 0:
            enemy_damage = enemy.attack
            self.player.take_damage(enemy_damage)
            console.print(f"{enemy.name} attacks you for {enemy_damage} damage!")
        else:
            console.print(f"[bold red]You defeated {enemy.name}![/bold red]")
            self.current_room.enemies.remove(enemy)

        # Narrative
        narrative = narrate_combat(
            player_action="attacked with a weapon",
            player_hp=self.player.hp,
            enemy_name=enemy.name,
            enemy_hp=max(0, enemy.hp),
            damage_dealt=damage,
        )
        console.print(f"[italic]{narrative}[/italic]")

    def handle_talk(self, parts: list):
        """Process the 'talk' command to converse with NPCs."""
        if not self.current_room or not self.current_room.npcs:
            console.print("There is no one here to talk to.")
            return

        if len(parts) == 1:
            console.print("Talk to whom?")
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
            console.print(f"No one named '{target_name}' here.")
            return

        console.print(
            f"[bold blue]You approach {npc.name}. (Type 'bye' or 'leave' to end the conversation)[/bold blue]"
        )
        history = ""
        while True:
            console.print("[cyan]You:[/cyan] ", end="")
            player_msg = self.get_input("").strip()
            if not player_msg:
                continue
            log_event("PLAYER_TALK", f"> {player_msg}")

            if player_msg.lower() in ["bye", "leave", "quit", "exit"]:
                console.print(
                    f"[bold blue]{npc.name} nods as you walk away.[/bold blue]"
                )
                break

            response = generate_npc_response(
                npc.name, npc.dialogue_context, player_msg, history
            )
            console.print(f"[bold blue]{npc.name}:[/bold blue] {response}")

            history += f"\nPlayer: {player_msg}\nNPC: {response}"
            if len(history) > 1000:
                history = history[-1000:]

    def handle_take(self, parts: list):
        """Process the 'take' command to pick up items."""
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
                console.print(f"You took the {item.name}.")
            else:
                console.print(f"No item named '{item_name}' here.")
        else:
            console.print("Take what?")

    def handle_use(self, parts: list):
        """Process the 'use' command for items in inventory."""
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
                if item.effect_type == "healing" and item.stat_effect:
                    effect_amount = item.stat_effect
                    self.player.heal(effect_amount)
                    console.print(
                        f"You used {item.name} and healed {effect_amount} HP."
                    )
                    self.player.inventory.remove(item)
                elif item.effect_type == "damage" and item.stat_effect:
                    console.print(f"You can't use {item.name} like that yet.")
                elif item.effect_type == "weapon":
                    console.print(
                        f"To use [bold cyan]{item.name}[/bold cyan], you must 'equip' it."
                    )
                else:
                    room_desc = (
                        self.current_room.description
                        if self.current_room
                        else "Unknown"
                    )
                    narration = narrate_item_use(item.name, item.description, room_desc)
                    console.print(f"[italic]{narration}[/italic]")
            else:
                console.print(f"You don't have an item named '{item_name}'.")
        else:
            console.print("Use what?")

    def handle_equip(self, parts: list):
        """Process the 'equip' command to equip a weapon."""
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
                        console.print(
                            f"You unequiped [bold cyan]{self.player.equipped_weapon.name}[/bold cyan]."
                        )
                    self.player.equipped_weapon = item
                    self.player.inventory.remove(item)
                    console.print(
                        f"You equipped [bold cyan]{item.name}[/bold cyan]! Your attack is now {self.player.total_attack}."
                    )
                else:
                    console.print(f"You can't equip {item.name}. It's not a weapon.")
            else:
                console.print(f"You don't have an item named '{item_name}'.")
        else:
            console.print("Equip what?")

    def handle_unequip(self):
        """Process the 'unequip' command to remove the current weapon."""
        if self.player.equipped_weapon:
            item = self.player.equipped_weapon
            self.player.inventory.append(item)
            self.player.equipped_weapon = None
            console.print(
                f"You unequiped [bold cyan]{item.name}[/bold cyan]. Your attack is now {self.player.total_attack}."
            )
        else:
            console.print("You don't have a weapon equipped.")
