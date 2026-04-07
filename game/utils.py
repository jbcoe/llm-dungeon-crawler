"""Utility functions for the game."""

from typing import Any


def get_model_name(m: Any) -> str:
    """Safely extract the model name from an Ollama model object or dict."""
    model_name: Any = ""
    if hasattr(m, "model"):
        model_name = getattr(m, "model", "")
    elif isinstance(m, dict):
        model_name = m.get("model", "") or m.get("name", "")

    return str(model_name or "")


def models_match(required: str, available: str) -> bool:
    """Check if two model names match, ignoring :latest tags."""
    if required == available:
        return True
    if ":" not in required and available == f"{required}:latest":
        return True
    if required.endswith(":latest") and available == required[: -len(":latest")]:
        return True
    return False
