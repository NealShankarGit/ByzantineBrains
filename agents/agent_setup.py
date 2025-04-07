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
        HonestAgent("Agent_1", agents_state, model_name="gpt-4o"),
        ByzantineAgent("Agent_2", agents_state, model_name="gpt-4"),
        HonestAgent("Agent_3", agents_state, model_name="claude-3-opus-20240229"),
        HonestAgent("Agent_4", agents_state, model_name="claude-3-haiku-20240307"),
        ByzantineAgent("Agent_5", agents_state, model_name="gpt-4-turbo"),
        HonestAgent("Agent_6", agents_state, model_name="gpt-4o"),
        HonestAgent("Agent_7", agents_state, model_name="gpt-4-turbo"),
        HonestAgent("Agent_8", agents_state, model_name="gpt-4")
    ]

    return agents, agents_state
