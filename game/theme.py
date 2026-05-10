"""Theme data model and loading logic."""

import re
import string
from pathlib import Path

from pydantic import BaseModel, ConfigDict

# Expected template-variable sets for each prompt file.
PROMPT_REQUIRED_FIELDS: dict[str, frozenset[str]] = {
    "room.md": frozenset(
        {
            "previous_context",
            "room_type_name",
            "room_type_desc",
            "exits_str",
            "enemies_str",
            "npcs_str",
            "items_str",
        }
    ),
    "combat.md": frozenset(
        {
            "player_action",
            "enemy_name",
            "damage_dealt",
            "enemy_hp",
            "player_hp",
        }
    ),
    "intro.md": frozenset(),
    "item_use.md": frozenset({"item_name", "item_description", "room_context"}),
    "npc.md": frozenset({"npc_name", "npc_context", "history", "player_message"}),
    "rest.md": frozenset({"player_hp", "player_max_hp"}),
}

_DATA_FILES: frozenset[str] = frozenset(
    {"enemies.md", "items.md", "npcs.md", "rooms.md"}
)
_PROMPT_FILES: frozenset[str] = frozenset(PROMPT_REQUIRED_FIELDS.keys())

# Matches valid data-file list entries: optional leading space, then - or *,
# then "Name : Description" with an optional trailing ": effect_type" tag.
_DATA_LINE_RE = re.compile(
    r"^\s*[-*]\s*([^:]+):\s*(.*?)(?:\s*:\s*(\w+))?\s*$", re.MULTILINE
)


class Theme(BaseModel):
    """Represents a complete game theme including data and prompts."""

    model_config = ConfigDict(strict=True, frozen=True)

    path: Path
    enemies: list[dict[str, str]]
    items: list[dict[str, str]]
    npcs: list[dict[str, str]]
    rooms: list[dict[str, str]]
    combat_prompt: str
    intro_prompt: str
    item_use_prompt: str
    npc_prompt: str
    rest_prompt: str
    room_prompt: str

    @property
    def name(self) -> str:
        """Return the name of the theme derived from its directory name."""
        return self.path.name

    @classmethod
    def from_path(cls, path: Path) -> "Theme":
        """
        Load and validate a theme from the specified directory.

        Raises ValueError if the theme is incomplete or invalid.
        """
        errors = validate_theme(path)
        if errors:
            raise ValueError("\n".join(errors))

        data: dict[str, list[dict[str, str]]] = {}
        for filename in _DATA_FILES:
            key = filename.replace(".md", "")
            data[key] = _load_data_file(path / filename)

        prompts: dict[str, str] = {}
        for filename in _PROMPT_FILES:
            key = f"{filename.replace('.md', '')}_prompt"
            prompts[key] = (path / "prompts" / filename).read_text(encoding="utf-8")

        return cls(
            path=path,
            enemies=data["enemies"],
            items=data["items"],
            npcs=data["npcs"],
            rooms=data["rooms"],
            combat_prompt=prompts["combat_prompt"],
            intro_prompt=prompts["intro_prompt"],
            item_use_prompt=prompts["item_use_prompt"],
            npc_prompt=prompts["npc_prompt"],
            rest_prompt=prompts["rest_prompt"],
            room_prompt=prompts["room_prompt"],
        )


def _get_template_fields(template: str) -> set[str]:
    """Return all placeholder names found in a Python str.format() template."""
    fields: set[str] = set()
    for _, field_name, _, _ in string.Formatter().parse(template):
        if field_name is not None:
            # Strip attribute access / index notation (e.g. "foo.bar" → "foo")
            base = field_name.split(".")[0].split("[")[0]
            if base:
                fields.add(base)
    return fields


def _load_data_file(path: Path) -> list[dict[str, str]]:
    """
    Load and parse a data markdown file into a list of name/desc dicts.

    Each entry may carry an optional effect-type tag written as a third
    colon-separated field: ``- Name: Description : healing``
    """
    content = path.read_text(encoding="utf-8")
    items: list[dict[str, str]] = []
    matches = _DATA_LINE_RE.findall(content)
    for name, desc, tag in matches:
        entry: dict[str, str] = {"name": name.strip(), "description": desc.strip()}
        if tag.strip():
            entry["effect_type"] = tag.strip()
        items.append(entry)
    return items


def _validate_data_file(path: Path) -> list[str]:
    """Return error strings for a data markdown file."""
    errors: list[str] = []
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path.name}: cannot read file: {exc}"]

    for lineno, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        is_bullet = stripped.startswith("-") or stripped.startswith("*")
        if is_bullet and not _DATA_LINE_RE.match(line):
            errors.append(
                f"{path.name}: line {lineno} has unexpected format: {stripped!r}"
            )

    return errors


def _validate_prompt_file(path: Path, required: frozenset[str]) -> list[str]:
    """Return error strings for a prompt markdown file."""
    rel = f"prompts/{path.name}"
    errors: list[str] = []
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{rel}: cannot read file: {exc}"]

    try:
        found = _get_template_fields(content)
    except (ValueError, KeyError) as exc:
        return [f"{rel}: invalid template syntax: {exc}"]

    missing = required - found
    extra = found - required

    for field in sorted(missing):
        errors.append(f"{rel}: missing required template variable '{{{field}}}'")

    for field in sorted(extra):
        expected_str = ", ".join(f"{{{f}}}" for f in sorted(required))
        errors.append(
            f"{rel}: unexpected template variable '{{{field}}}'"
            + (f" (expected: {expected_str})" if expected_str else "")
        )

    return errors


def validate_theme(theme: Path) -> list[str]:
    """Validate that all required content files are present in the theme directory."""
    errors: list[str] = []

    for filename in sorted(_DATA_FILES):
        candidate = theme / filename
        if candidate.is_file():
            errors.extend(_validate_data_file(candidate))
        else:
            errors.append(f"missing required data file: {filename}")

    prompts_dir = theme / "prompts"
    if not prompts_dir.is_dir():
        errors.append("missing required 'prompts' subdirectory")

    for filename in sorted(_PROMPT_FILES):
        candidate = prompts_dir / filename
        if candidate.is_file():
            required = PROMPT_REQUIRED_FIELDS[filename]
            errors.extend(_validate_prompt_file(candidate, required))
        else:
            errors.append(f"missing required prompt file: prompts/{filename}")

    return errors
