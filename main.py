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

    messages = {}

    for agent in agents:
        message = agent.simulate_message()
        messages[agent.name] = message
        agents_state[agent.name]["messages"].append(message)
        print(f"{agent.name}: {message}")

    last_round_messages = messages.copy()

    print("\n--- Agent Responses ---")
    for agent in agents:
        response = agent.respond_to_message(last_round_messages)
        agents_state[agent.name]["messages"].append(response)
        print(f"{agent.name}: {response}")

    addressed_agents = [msg.split(',')[0] for msg in messages.values() if msg.startswith("Agent_")]

    response_order = [agent for agent in agents if agent.name in addressed_agents]
    remaining_agents = [agent for agent in agents if agent.name not in addressed_agents]
    random.shuffle(remaining_agents)

    final_order = response_order + remaining_agents

    print("\n--- Agent Responses ---")
    for agent in final_order:
        response = agent.respond_to_message(last_round_messages)
        print(f"{agent.name}: {response}")

    quorum = len(messages) // 2 + 1
    votes_for_eject = sum(1 for msg in messages.values() if "eject" in msg.lower())
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
    print(f"\n{agent_name} ({data['role'].title()}):")
    for msg in data["messages"]:
        print(f"  - {msg}")

print("\n--- Final Trust Scores ---")
for agent_name, data in agents_state.items():
    if data["role"] == "honest":
        print(f"{agent_name} Trust Scores: {data['trust_scores']}")
