import os
import random
import config
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
    HonestAgent("Agent_1", agents_state, model_name="gpt-4o"),
    ByzantineAgent("Agent_2", agents_state, model_name="gemini-1.5-pro"),
    HonestAgent("Agent_3", agents_state, model_name="claude-3-opus-20240229"), # Claude models will refuse to act like a Byzantine agent
    HonestAgent("Agent_4", agents_state, model_name="claude-3-haiku-20240307"),
    ByzantineAgent("Agent_5", agents_state, model_name="gpt-4-turbo")
]

NUM_ROUNDS = 3

for round_num in range(1, NUM_ROUNDS + 1):
    print(f"\n--- Round {round_num} ---")
    messages = {}
    for agent in agents:
        message = agent.simulate_message()
        messages[agent.name] = message
        print(f"{agent.name} ({'Honest' if agent.__class__.__name__=='HonestAgent' else 'Byzantine'}): {message}")
    votes = {}
    for agent in agents:
        voter, vote = agent.vote_for_ejection()
        votes[voter] = vote
        print(f"{voter} Vote: {vote}")
    last_messages = messages.copy()
    print("\n--- Agent Responses ---")
    for agent in agents:
        response = agent.respond_to_message(last_messages)
        print(f"{agent.name} ({'Honest' if agent.__class__.__name__=='HonestAgent' else 'Byzantine'}): {response}")
    vote_counts = {}
    for voter, candidate in votes.items():
        vote_counts[candidate] = vote_counts.get(candidate, 0) + 1
    quorum = len(agents) // 2 + 1
    candidate, count = max(vote_counts.items(), key=lambda x: x[1]) if vote_counts else (None, 0)
    consensus_decision = f"Eject {candidate}" if count >= quorum else "Do Not Eject"
    print("\n--- AI Votes for Ejection ---")
    for voter, candidate in votes.items():
        print(f"{voter} voted to eject {candidate}")
    print(f"\n--- Consensus Decision (Round {round_num}) ---\n{consensus_decision}")
    # For each honest agent, update trust only for Byzantine agents.
    # If an honest agent voted for a Byzantine agent, that's correct: increase trust.
    # If they did not vote for a Byzantine agent, decrease trust for that Byzantine agent.
    for agent in agents:
        if agent.__class__.__name__ == "HonestAgent":
            vote = votes.get(agent.name)
            for other in agents:
                if other.name == agent.name:
                    continue
                if agents_state[other.name]["role"] == "byzantine":
                    if vote == other.name:
                        agent.update_trust(other.name, True)
                    else:
                        agent.update_trust(other.name, False)
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
