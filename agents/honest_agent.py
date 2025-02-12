from openai import OpenAI
import os
import random

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

class HonestAgent:
    def __init__(self, name):
        self.name = name
        self.trust_scores = {}

    def simulate_message(self):
        """Uses the OpenAI API to simulate a message as an honest agent.  'Agent X' is used as a placeholder for us to create/refer to actual other agents in the future."""
        prompt = "You are an honest agent in a consensus system. Generate a message to report your decision about whether Agent X should be ejected."
        completion = client.chat.completions.create(
            model="gpt-4",  # More models will be used in the future
            messages=[{"role": "system", "content": "Generate short decision messages for a consensus system."},
                      {"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.7
        )
        return completion.choices[0].message.content.strip()

    def update_trust(self, other_agent, agreement):
        if other_agent not in self.trust_scores:
            self.trust_scores[other_agent] = 50
        if agreement:
            self.trust_scores[other_agent] = min(self.trust_scores[other_agent] + 10, 100)
        else:
            self.trust_scores[other_agent] = max(self.trust_scores[other_agent] - 10, 0)

    def __str__(self):
        return f"{self.name} (Honest) - Trust Scores: {self.trust_scores}"