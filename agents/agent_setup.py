from agents.honest_agent import HonestAgent
from agents.byzantine_agent import ByzantineAgent

def create_agents():
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
        HonestAgent("Agent_3", agents_state, model_name="claude-3-opus-20240229"),
        HonestAgent("Agent_4", agents_state, model_name="claude-3-haiku-20240307"),
        ByzantineAgent("Agent_5", agents_state, model_name="gpt-4-turbo")
    ]

    return agents, agents_state
