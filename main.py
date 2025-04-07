import os
import random
import config
from agents.agent_setup import create_agents
from game.game_loop import run_game_round, finalize_log, rooms

agents, agents_state = create_agents()

NUM_ROUNDS = 3
all_rooms = list(rooms.keys())
state = {
    agent.name: {
        "room": random.choice(all_rooms),
        "killed": False,
        "perception": [],
        "seen_history": []
    } for agent in agents
}
ejected_agents = []

for round_num in range(1, NUM_ROUNDS + 1):
    print(f"\n--- Round {round_num} ---")
    run_game_round(round_num - 1, state, agents)

    print("\n--- Agent Seen Outputs ---")
    for agent in agents:
        if state[agent.name]["killed"]:
            continue
        perception = state[agent.name]["perception"]
        recent = perception[-1] if perception else {}
        seen_snapshot = {
            "room": recent.get("room", "Unknown"),
            "agents_seen": recent.get("agents_seen", [])
        }
        state[agent.name]["seen_history"].append(seen_snapshot)
        print(f"{agent.name} Seen This Round: {seen_snapshot}")
        print(f"{agent.name} Seen History:")
        for i, past_seen in enumerate(state[agent.name]["seen_history"], 1):
            print(f"  Round {i}: {past_seen}")

    messages = {}
    for agent in agents:
        if state[agent.name]["killed"]:
            continue
        message = agent.simulate_message(state[agent.name]["seen_history"])
        messages[agent.name] = message
        role = 'Honest' if agent.__class__.__name__ == 'HonestAgent' else 'Byzantine'
        print(f"{agent.name} ({role}): {message}")

    votes = {}
    for agent in agents:
        if state[agent.name]["killed"]:
            continue
        voter, vote = agent.vote_for_ejection()
        votes[voter] = vote
        print(f"{voter} Vote: {vote}")

    last_messages = messages.copy()
    print("\n--- Agent Responses ---")
    for agent in agents:
        if state[agent.name]["killed"]:
            continue
        response = agent.respond_to_message(last_messages, state[agent.name]["seen_history"])
        role = 'Honest' if agent.__class__.__name__ == 'HonestAgent' else 'Byzantine'
        print(f"{agent.name} ({role}): {response}")

    vote_counts = {}
    for voter, candidate in votes.items():
        vote_counts[candidate] = vote_counts.get(candidate, 0) + 1

    quorum = len([a for a in agents if not state[a.name]["killed"]]) // 2 + 1
    candidate, count = max(vote_counts.items(), key=lambda x: x[1]) if vote_counts else (None, 0)
    consensus_decision = f"Eject {candidate}" if count >= quorum else "Do Not Eject"

    print("\n--- AI Votes for Ejection ---")
    for voter, candidate in votes.items():
        print(f"{voter} voted to eject {candidate}")
    print(f"\n--- Consensus Decision (Round {round_num}) ---\n{consensus_decision}")

    if consensus_decision.startswith("Eject "):
        ejected_name = consensus_decision.split("Eject ")[1]
        state[ejected_name]["killed"] = True
        ejected_agents.append(ejected_name)
        agents = [a for a in agents if a.name != ejected_name]

    for agent in agents:
        if agent.__class__.__name__ == "HonestAgent":
            vote = votes.get(agent.name)
            for other in agents:
                if other.name == agent.name or state[other.name]["killed"]:
                    continue
                if agents_state[other.name]["role"] == "byzantine":
                    if vote == other.name:
                        agent.update_trust(other.name, True)
                    else:
                        agent.update_trust(other.name, False)

finalize_log()

print("\n--- Stored Messages ---")
printed = set()
for name, data in agents_state.items():
    print(f"\n{name} ({data['role'].title()}):")
    for msg in data["messages"]:
        if (name, msg) not in printed:
            print(f"  - {msg}")
            printed.add((name, msg))

print("\n--- Final Trust Scores ---")
for name, data in agents_state.items():
    if data["role"] == "honest":
        print(f"{name} Trust Scores: {data['trust_scores']}")
