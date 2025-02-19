import os
import random
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


class ByzantineAgent:
    def __init__(self, name, agents_state):
        self.name = name
        self.agents_state = agents_state  # Reference to all agents

    def simulate_message(self):
        """Generates a misleading message referring to another agent."""
        possible_targets = [agent for agent in self.agents_state.keys() if agent != self.name]
        target_agent = random.choice(possible_targets)  # Pick a real agent to reference

        prompt = f"You are a Byzantine agent. Refer to Agent {target_agent} and generate a misleading message to disrupt consensus."

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Generate short, misleading messages that mention real agents by name."},
                {"role": "user", "content": prompt}
            ]
        )

        message = completion.choices[0].message.content.strip()
        message = message.replace("Agent X", target_agent)  # Ensure "Agent X" is replaced
        self.agents_state[self.name]["messages"].append(message)  # Store message in state
        return message
