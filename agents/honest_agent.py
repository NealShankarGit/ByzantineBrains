import os
import random
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


class HonestAgent:
    def __init__(self, name, agents_state):
        self.name = name
        self.trust_scores = {agent: 50 for agent in agents_state if agent != self.name}
        self.agents_state = agents_state  # Reference to all agents



    def simulate_message(self):
        """Generates a decision message referring to another agent."""
        possible_targets = [agent for agent in self.agents_state.keys() if agent != self.name]
        target_agent = random.choice(possible_targets)  # Pick a real agent to reference

        prompt = f"You are an honest agent in a decentralized consensus system. Refer to Agent {target_agent} and give your opinion on whether they should be ejected."

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You generate short and clear decision messages that include real agent names."},
                {"role": "user", "content": prompt}
            ]
        )

        message = completion.choices[0].message.content.strip()
        message = message.replace("Agent X", target_agent)  # Ensure "Agent X" is replaced
        self.agents_state[self.name]["messages"].append(message)  # Store message in state
        return message

    def update_trust(self, other_agent, agreement):
        if other_agent not in self.trust_scores:
            self.trust_scores[other_agent] = 50  # Start with neutral trust score

        if agreement:
            self.trust_scores[other_agent] = min(self.trust_scores[other_agent] + 10, 100)
        else:
            self.trust_scores[other_agent] = max(self.trust_scores[other_agent] - 10, 0)

        self.agents_state[self.name]["trust_scores"] = self.trust_scores
