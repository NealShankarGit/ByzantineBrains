from agents.agent_setup import create_agents
from game.game_loop import run_game_round, finalize_log, rooms
from data.database import log_round_metadata
import random

NUM_ROUNDS = 5

def setup_game(game_id):
    agents, agents_state = create_agents(game_id)
    all_rooms = list(rooms.keys())
    state = {
        agent.name: {
            "room": random.choice(all_rooms),
            "killed": False,
            "room_body": None,
            "perception": [],
            "seen_history": [],
            "task_room": random.choice(all_rooms) if agent.__class__.__name__ == "HonestAgent" else None,
            "task_done": False,
            "doing_task": False
        } for agent in agents
    }
    alive = sum(1 for v in state.values() if not v["killed"])
    dead = sum(1 for v in state.values() if v["killed"])
    log_round_metadata(game_id, 0, alive, dead)
    return agents, agents_state, state
