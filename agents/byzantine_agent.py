from openai import OpenAI
import os
import random

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

class ByzantineAgent:
    def __init__(self, name):
        self.name = name

    def simulate_message(self):
        behaviors = [
            "You are a malicious agent. Generate a misleading message to disrupt consensus.",
            "You are a Byzantine agent. Generate a random, conflicting message about whether Agent X should be ejected."
        ]
        prompt = random.choice(behaviors)
        completion = client.chat.completions.create(
            model="gpt-4",  # More models will be used in future
            messages=[{"role": "system", "content": "Generate short, disruptive messages."},
                      {"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=1.0
        )
        return completion.choices[0].message.content.strip()

    def __str__(self):
        return f"{self.name} (Byzantine)"