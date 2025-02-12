import random
from agents.honest_agent import HonestAgent
from agents.byzantine_agent import ByzantineAgent
from core.consensus_module import reach_consensus

# Will be randomized in future update
agents = [
    HonestAgent("Agent_1"),
    HonestAgent("Agent_2"),
    ByzantineAgent("Agent_3"),
    HonestAgent("Agent_4"),
    ByzantineAgent("Agent_5")
]

print("\n--- Message Exchange ---")
messages = []
for agent in agents:
    message = agent.simulate_message()
    messages.append(message)
    print(f"{agent.name}: {message}")

consensus_result = reach_consensus(messages)
print("\n--- Consensus Module Result ---")
print(consensus_result)

# Update trust scores for honest agents only
for agent in agents:
    if isinstance(agent, HonestAgent):
        for other_agent in agents:
            if other_agent != agent:
                agent.update_trust(other_agent.name, consensus_result["consensus_decision"] == "Eject Agent X")

print("\n--- Final Trust Scores ---")
for agent in agents:
    if isinstance(agent, HonestAgent):
        print(agent)