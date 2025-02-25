import os
import random
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


class ByzantineAgent:
    def __init__(self, name, agents_state):
        self.name = name
        self.agents_state = agents_state

    def simulate_message(self):
        possible_targets = [agent for agent in self.agents_state.keys() if agent != self.name]
        target_agent = random.choice(possible_targets)

        past_messages = self.agents_state[self.name]["messages"][-3:]
        message_history = "\n".join(past_messages) if past_messages else "No prior messages."

        prompt = f"""
        You are Agent {self.name}, a Byzantine agent attempting to disrupt consensus. 
        Previous messages from you:
        {message_history}

        Address Agent {target_agent} directly and generate a misleading response.
        Example: 'Agent_3, you are clearly lying about the last vote. We should not trust you.'
        """

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Generate deceptive messages that address specific agents by name."},
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
        You are Agent {self.name}, a Byzantine agent attempting to manipulate the consensus.
        Here is the full conversation history:
        {conversation_history}

        Review the messages and determine if you were addressed.
        - If you were directly mentioned, respond in a way that continues to create confusion.
        - If you were not mentioned, provide a misleading general comment that shifts attention elsewhere.
        - Keep your response to one line and less than 100 words.
        """

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "Generate misleading responses that either directly address prior messages or introduce confusion."},
                {"role": "user", "content": prompt}
            ]
        )

        response = completion.choices[0].message.content.strip()
        self.agents_state[self.name]["messages"].append(response)
        return response


