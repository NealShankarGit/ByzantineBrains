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

    agents = []
    for i in range(1, 9):
        name = f"Agent_{i}"
        if i in [2, 5]:
            agents.append(ByzantineAgent(name, agents_state, model_name="gpt-4"))
        else:
            agents.append(HonestAgent(name, agents_state, model_name="gpt-4"))

    return agents, agents_state
