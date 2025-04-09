from agents.honest_agent import HonestAgent
from agents.byzantine_agent import ByzantineAgent

def create_agents():
    agents_state = {
        f"Agent_{i}": {
            "role": "byzantine" if i in [2, 5] else "honest",
            "trust_scores": {},
            "messages": [],
            "perception": []
        }
        for i in range(1, 9)
    }

    agents = [
        HonestAgent("Agent_1", agents_state, model_name="gpt-4o", color="🔴"),
        ByzantineAgent("Agent_2", agents_state, model_name="gpt-4", color="🔵"),
        HonestAgent("Agent_3", agents_state, model_name="claude-3-opus-20240229", color="🟢"),
        HonestAgent("Agent_4", agents_state, model_name="claude-3-haiku-20240307", color="💗"),
        ByzantineAgent("Agent_5", agents_state, model_name="gpt-4-turbo", color="🟠"),
        HonestAgent("Agent_6", agents_state, model_name="gpt-4o", color="🟡"),
        HonestAgent("Agent_7", agents_state, model_name="gpt-4-turbo", color="⚫"),
        HonestAgent("Agent_8", agents_state, model_name="gpt-4", color="⚪")
    ]

    return agents, agents_state
