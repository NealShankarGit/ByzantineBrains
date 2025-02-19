import random
from agents.honest_agent import HonestAgent
from agents.byzantine_agent import ByzantineAgent

agents_state = {
    "Agent_1": {"role": "honest", "trust_scores": {}, "messages": []},
    "Agent_2": {"role": "byzantine", "trust_scores": {}, "messages": []},
    "Agent_3": {"role": "honest", "trust_scores": {}, "messages": []},
    "Agent_4": {"role": "honest", "trust_scores": {}, "messages": []},
    "Agent_5": {"role": "byzantine", "trust_scores": {}, "messages": []}
}

agents = [
    HonestAgent("Agent_1", agents_state),
    ByzantineAgent("Agent_2", agents_state),
    HonestAgent("Agent_3", agents_state),
    HonestAgent("Agent_4", agents_state),
    ByzantineAgent("Agent_5", agents_state)
]

NUM_ROUNDS = 3

for round_num in range(1, NUM_ROUNDS + 1):
    print(f"\n--- Round {round_num} ---")

    messages = []
    for agent in agents:
        message = agent.simulate_message()
        messages.append(message)
        print(f"{agent.name}: {message}")

    quorum = len(messages) // 2 + 1
    votes_for_eject = sum(1 for msg in messages if "eject" in msg.lower())
    consensus_decision = "Eject " + random.choice(
        list(agents_state.keys())) if votes_for_eject >= quorum else "Do Not Eject"

    print(f"\n--- Consensus Decision (Round {round_num}) ---\n{consensus_decision}")

    for agent in agents:
        if isinstance(agent, HonestAgent):
            for other_agent in agents:
                if other_agent.name != agent.name:
                    agent.update_trust(other_agent.name, consensus_decision == "Eject " + other_agent.name)

print("\n--- Stored Messages ---")
for agent_name, data in agents_state.items():
    print(f"{agent_name} ({data['role'].title()}): {data['messages']}")

print("\n--- Final Trust Scores ---")
for agent_name, data in agents_state.items():
    if data["role"] == "honest":
        print(f"{agent_name} Trust Scores: {data['trust_scores']}")
