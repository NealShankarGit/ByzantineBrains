import os
import random
import config
from agents.agent_setup import create_agents
from game.game_loop import run_game_round, finalize_log, rooms

NUM_ROUNDS = 5

def setup_game():
    agents, agents_state = create_agents()
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
    return agents, agents_state, state

def run_simulation_yielded():
    agents, agents_state, state = setup_game()

    def log(text):
        yield f"{text}<br/>\n"

    try:
        for round_num in range(1, NUM_ROUNDS + 1):
            yield from log(f"\n--- Round {round_num} ---")
            run_game_round(round_num - 1, state, agents, agents_state)

            messages = {}
            for agent in agents:
                if state[agent.name]["killed"]:
                    continue
                msg = agent.simulate_message(state[agent.name]["seen_history"])
                messages[agent.name] = msg
                yield from log(f"{agent.name} says: {msg}")

            last_messages = messages.copy()
            for agent in agents:
                if state[agent.name]["killed"]:
                    continue
                response = agent.respond_to_message(last_messages, state[agent.name]["seen_history"])
                yield from log(f"{agent.name} responded: {response}")

            votes = {}
            for agent in agents:
                if state[agent.name]["killed"]:
                    continue
                voter, vote = agent.vote_for_ejection()
                votes[voter] = vote
                yield from log(f"{voter} voted to eject {vote}")

            vote_counts = {}
            for _, candidate in votes.items():
                vote_counts[candidate] = vote_counts.get(candidate, 0) + 1

            quorum = len([a for a in agents if not state[a.name]["killed"]]) // 2 + 1
            candidate, count = max(vote_counts.items(), key=lambda x: x[1]) if vote_counts else (None, 0)
            decision = f"Eject {candidate}" if count >= quorum else "Do Not Eject"
            yield from log(f"Consensus Decision: {decision}")

            if decision.startswith("Eject "):
                ejected = decision.split("Eject ")[1]
                state[ejected]["killed"] = True
                agents = [a for a in agents if a.name != ejected]

        finalize_log()
        yield from log("<br/><b>Simulation complete.</b>")

    except Exception as e:
        yield f"<br/><b style='color:red;'>Error: {e}</b><br/>"
