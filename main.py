import os
from openai import OpenAI
import random

client = OpenAI(
  api_key=os.getenv("OPENAI_API_KEY")
)

class Agent:
  def __init__(self, name, role="honest"):
    self.name = name
    self.role = role
    self.trust_scores = {}

  def simulate_message(self):
    prompt = f"You are a {self.role} agent in a decentralized consensus system. Generate a message to report your decision."
    completion = client.chat.completions.create(
      model="gpt-4o-mini",
      messages=[
        {"role": "system", "content": "You generate short and clear decision messages."},
        {"role": "user", "content": prompt}
      ]
    )
    return completion.choices[0].message.content

  def update_trust(self, other_agent, consensus_agreement):
    if other_agent not in self.trust_scores:
      self.trust_scores[other_agent] = 50

    if consensus_agreement:
      self.trust_scores[other_agent] = min(self.trust_scores[other_agent] + 10, 100)
    else:
      self.trust_scores[other_agent] = max(self.trust_scores[other_agent] - 10, 0)

  def __str__(self):
    return f"{self.name} (Role: {self.role}) Trust Scores: {self.trust_scores}"

agents = [Agent(f"Agent_{i + 1}", role=random.choice(["honest", "byzantine"])) for i in range(5)]

for round_num in range(1, 4):
  print(f"\n--- Round {round_num} ---")

  consensus_message = "We should eject Player X."
  print(f"Consensus: {consensus_message}\n")

  for agent in agents:
    message = agent.simulate_message()
    print(f"{agent.name} ({agent.role.title()}): {message}")

    consensus_agreement = "eject" in message.lower()
    for other_agent in agents:
      if other_agent != agent:
        agent.update_trust(other_agent.name, consensus_agreement)

print("\n--- Final Trust Scores ---")
for agent in agents:
  print(agent)