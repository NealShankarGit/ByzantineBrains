import os
import random
import re
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.7, openai_api_key=os.getenv("OPENAI_API_KEY"))

class ByzantineAgent:
    def __init__(self, name, agents_state):
        self.name = name
        self.agents_state = agents_state

    def simulate_message(self):
        full_message_history = "\n".join(
            [f"{agent}: {msg}" for agent, msgs in self.agents_state.items() for msg in msgs["messages"]]
        ) if any(self.agents_state[agent]["messages"] for agent in self.agents_state) else "No prior messages."

        prompt = f"""
        You are Agent {self.name}, a Byzantine agent attempting to manipulate other agents to incorrectly identify honest agents as Byzantine agents.
        Here is the entire conversation history:
        {full_message_history}

        Choose which agent(s) to address based on the discussion:
        - If you can shift blame, introduce uncertainty or doubt.
        - If you can disrupt trust between agents, do so subtly.
        - If no one has mentioned you, introduce a misleading but plausible narrative.
        - Try to suggest that other agents are Byzantine agents by reading the conversation history and looking for players with weak alliances.
        - Keep your response to one line and less than 25 words.
        """

        messages = [
            SystemMessage(content="Generate deceptive messages that address specific agents by name."),
            HumanMessage(content=prompt)
        ]

        response = llm.invoke(messages)

        message = response.content.strip()
        self.agents_state[self.name]["messages"].append(message)
        return message

    def respond_to_message(self, last_messages):
        conversation_history = "\n".join([f"{agent}: {msg}" for agent, msg in last_messages.items() if msg])
        prompt = f"""
        You are Agent {self.name}, a Byzantine agent attempting to manipulate other agents to incorrectly identify honest agents as Byzantine agents.
        Here is the full conversation history:
        {conversation_history}

        Review the messages and determine if you were addressed.
        - If you were directly mentioned, respond in a way that continues to manipulate.
        - If you were not mentioned, provide a misleading general comment that shifts attention elsewhere or towards another agent.
        - Try to suggest that other agents are Byzantine agents by reading the conversation history and looking for players with weak alliances.
        - Keep your response to one line and less than 25 words.
        """

        messages = [
            SystemMessage(content="Generate misleading responses that either directly address prior messages or introduce confusion."),
            HumanMessage(content=prompt)
        ]

        response = llm.invoke(messages).content.strip()

        if response not in self.agents_state[self.name]["messages"]:
            self.agents_state[self.name]["messages"].append(response)

        return response

    def vote_for_ejection(self):
        full_message_history = "\n".join(
            [f"{agent}: {msg}" for agent, msgs in self.agents_state.items() for msg in msgs["messages"]]
        ) if any(self.agents_state[agent]["messages"] for agent in self.agents_state) else "No prior messages."

        prompt = f"""
        You are Agent {self.name}, a Byzantine agent attempting to manipulate the voting process and mislead others into ejecting an innocent agent.

        Here is the entire conversation history:
        {full_message_history}

        Vote for ONE other agent to be ejected based on how you can mislead the group. Only return the agent's name (e.g., 'Agent_5'). If no one should be ejected, return 'No Ejection'.
        """

        messages = [
            SystemMessage(content="Vote strategically to mislead the group."),
            HumanMessage(content=prompt)
        ]

        vote_response = llm.invoke(messages).content.strip()

        return self.name, vote_response
