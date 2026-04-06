from game.engine import GameEngine
from game.models import Room


def test_engine_initialization(mock_ai_api):
    mock_gen_room, _, _, _, _ = mock_ai_api
    engine = GameEngine(mock_input=["quit"])
    engine.start()

    assert engine.player.hp == 100
    assert engine.floor == 1
    assert engine.current_room is not None
    assert engine.current_room.description == "A mocked room."
    assert "north" in engine.current_room.exits
    mock_gen_room.assert_called_once()


def test_combat(mock_ai_api):
    _, mock_narrate, _, _, _ = mock_ai_api
    engine = GameEngine(mock_input=["attack slime", "quit"])
    room = Room(
        description="Test",
        exits=["north"],
        enemies=[
            {
                "name": "Slime",
                "description": "test",
                "hp": 10,
                "max_hp": 10,
                "attack": 2,
            }
        ],
    )
    engine.current_room = room
    engine.game_loop()

    # Slime should have taken 10 damage from player's attack of 10 and died
    assert len(engine.current_room.enemies) == 0
    # Player takes no damage because slime died before it could attack
    assert engine.player.hp == 100
    mock_narrate.assert_called_once()


def test_talk(mock_ai_api):
    _, _, mock_npc_resp, _, _ = mock_ai_api
    engine = GameEngine(mock_input=["talk merchant", "hello", "bye", "quit"])
    room = Room(
        description="Test",
        exits=["north"],
        npcs=[
            {
                "name": "Merchant",
                "description": "A merchant",
                "dialogue_context": "Friendly",
            }
        ],
    )
    engine.current_room = room
    engine.game_loop()

    mock_npc_resp.assert_called_once()
