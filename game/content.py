"""Validation of alternative content directories for theme support."""

import re
import string
from pathlib import Path

# Expected template-variable sets for each prompt file.
# Prompts that take no variables map to an empty frozenset.
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
# then "Name : Description"
_DATA_LINE_RE = re.compile(r"^\s*[-*]\s*([^:]+):\s*(.*)$")


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


def _validate_data_file(path: Path) -> list[str]:
    """
    Return error strings for a data markdown file.

    Checks that the file contains at least one valid ``- Name: Description``
    entry and that every non-blank, non-header line follows that format.
    """
    errors: list[str] = []
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path.name}: cannot read file: {exc}"]

    valid_count = 0
    for lineno, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue  # blank lines and markdown headers are fine
        if _DATA_LINE_RE.match(line):
            valid_count += 1
        else:
            errors.append(
                f"{path.name}: line {lineno} has unexpected format "
                f"(expected '- Name: Description'): {stripped!r}"
            )

    if valid_count == 0:
        errors.append(
            f"{path.name}: no valid entries found. "
            "Add at least one '- Name: Description' line."
        )

    return errors


def _validate_prompt_file(path: Path, required: frozenset[str]) -> list[str]:
    """
    Return error strings for a prompt markdown file.

    Checks that the template contains exactly the expected set of
    ``{variable}`` placeholders — no more, no fewer.
    """
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


def validate_content_dir(content_dir: Path) -> list[str]:
    """
    Validate all content files present in *content_dir*.

    Only files that exist inside the directory are checked — absent files are
    silently skipped (they fall back to the built-in equivalents at runtime).

    Returns a (possibly empty) list of human-readable error strings.
    """
    errors: list[str] = []

    for filename in sorted(_DATA_FILES):
        candidate = content_dir / filename
        if candidate.is_file():
            errors.extend(_validate_data_file(candidate))

    prompts_dir = content_dir / "prompts"
    for filename in sorted(_PROMPT_FILES):
        candidate = prompts_dir / filename
        if candidate.is_file():
            required = PROMPT_REQUIRED_FIELDS[filename]
            errors.extend(_validate_prompt_file(candidate, required))

    return errors
