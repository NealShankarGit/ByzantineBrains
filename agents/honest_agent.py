import os
from openai import OpenAI
import random

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

class HonestAgent:
    def __init__(self, name, agents_state):
        self.name = name
        self.trust_scores = {agent: 50 for agent in agents_state if agent != self.name}
        self.agents_state = agents_state

    def simulate_message(self):
        possible_targets = [agent for agent in self.agents_state.keys() if agent != self.name]
        target_agent = random.choice(possible_targets)

        past_messages = self.agents_state[self.name]["messages"][-3:]
        message_history = "\n".join(past_messages) if past_messages else "No prior messages."

        prompt = f"""
        You are Agent {self.name}, an honest agent in a decentralized consensus system. 
        Previous messages from you:
        {message_history}

        Address Agent {target_agent} directly and respond to whether they should be ejected or not.
        Example: 'Agent_5, you have been inconsistent in your statements. I vote to eject you.'
        """

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You generate short, clear decision messages addressing other agents by name."},
                {"role": "user", "content": prompt}
            ]
        )

        message = completion.choices[0].message.content.strip()
        message = message.replace("Agent X", target_agent)
        self.agents_state[self.name]["messages"].append(message)
        return message

    def respond_to_message(self, last_messages):
        conversation_history = "\n".join([f"{agent}: {msg}" for agent, msg in last_messages.items() if msg])
        prompt = f"""
        You are Agent {self.name}, an honest agent in a decentralized system.
        Here is the full conversation history:
        {conversation_history}

        Review the messages and determine if you were addressed.
        - If you were directly mentioned, respond logically.
        - If you were not mentioned, provide your general thoughts on the current situation.
        - Keep your response to one line and less than 100 words.
        """

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You generate concise responses, responding directly if mentioned, or giving general thoughts if not."},
                {"role": "user", "content": prompt}
            ]
        )

        response = completion.choices[0].message.content.strip()
        self.agents_state[self.name]["messages"].append(response)
        return response

    def update_trust(self, other_agent, agreement):
        if other_agent not in self.trust_scores:
            self.trust_scores[other_agent] = 50

        if agreement:
            self.trust_scores[other_agent] = min(self.trust_scores[other_agent] + 10, 100)
        else:
            self.trust_scores[other_agent] = max(self.trust_scores[other_agent] - 10, 0)

        self.agents_state[self.name]["trust_scores"] = self.trust_scores
