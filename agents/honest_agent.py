import os
import random
import re
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

class HonestAgent:
    def __init__(self, name, agents_state):
        self.name = name
        self.trust_scores = {agent: 50 for agent in agents_state if agent != self.name}
        self.agents_state = agents_state

    def simulate_message(self):

        full_message_history = "\n".join(
            [f"{agent}: {msg}" for agent, msgs in self.agents_state.items() for msg in msgs["messages"]]
        ) if any(self.agents_state[agent]["messages"] for agent in self.agents_state) else "No prior messages."

        prompt = f"""
        You are Agent {self.name}, an honest agent in a decentralized consensus system. You are attempting to identify the Byzantine agent(s) to eject.
        Here is the entire conversation history:
        {full_message_history}

        Decide which agent(s) to address based on the discussion:
        - If an agent's actions need to be questioned, call them out.
        - If a debate is forming, contribute to it.
        - If no one directly mentioned you, provide a general strategic observation.
        - Try to guess who the Byzantine agent is.
        - Keep your response to one line and less than 25 words.
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
        clean_message = re.sub(rf"^{self.name}[:,\s]+", "", message).strip()
        self.agents_state[self.name]["messages"].append(clean_message)
        return message

    def respond_to_message(self, last_messages):
        conversation_history = "\n".join([f"{agent}: {msg}" for agent, msg in last_messages.items() if msg])
        prompt = f"""
        You are Agent {self.name}, an honest agent in a decentralized consensus system. You are attempting to identify the Byzantine agent(s) to eject.
        Here is the full conversation history:
        {conversation_history}

        Review the messages and determine if you were addressed.
        - If you were directly mentioned, respond logically.
        - If you were not mentioned, provide your general thoughts on the current situation.
        - Try to guess who the Byzantine agent is.
        - Keep your response to one line and less than 25 words.
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
        if response not in self.agents_state[self.name]["messages"]:
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
