"""Shared test fixtures for the game."""

import pytest

from game.ai import AIGenerator
from game.logger import log_event


class FakeAIGenerator(AIGenerator):
    """Test double for AIGenerator to bypass network calls."""

    def __init__(self) -> None:
        """Initialize the fake AI generator."""
        super().__init__(model="test-model")

    def _query_model(self, prompt: str, system_message: str | None = None) -> str:
        log_event(f"API_CALL: {self.model}", prompt)
        content = "Simulated AI response."
        log_event(f"API_RESPONSE: {self.model}", content)
        return content


@pytest.fixture
def fake_ai() -> FakeAIGenerator:
    """Return an instance of FakeAIGenerator."""
    return FakeAIGenerator()
