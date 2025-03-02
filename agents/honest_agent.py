import os
import random
import re
import litellm
from langchain.schema import SystemMessage, HumanMessage
from langchain.schema.runnable import RunnableSequence
from langchain.prompts import PromptTemplate

llm = lambda prompt: litellm.completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": str(prompt)}],
    temperature=0.7
)
class HonestAgent:
    def __init__(self, name, agents_state):
        self.name = name
        self.trust_scores = {agent: 50 for agent in agents_state if agent != self.name}
        self.agents_state = agents_state

        self.chain = (
            PromptTemplate(
                input_variables=["name", "history"],
                template="""
                You are Agent {name}, an honest agent in a decentralized consensus system. Your goal is to identify the Byzantine agent(s) to eject.
                Here is the conversation history:
                {history}

                Choose how to contribute:
                - If an agent seems suspicious, call them out.
                - If a debate is forming, provide your perspective.
                - If no one mentioned you, share a strategic observation.
                - Try to determine who the Byzantine agent is.
                - Keep your response to one line and under 25 words.
                """
            )
            | llm
        )

    def simulate_message(self):
        full_message_history = "\n".join(
            [f"{agent}: {msg}" for agent, msgs in self.agents_state.items() for msg in msgs["messages"]]
        ) if any(self.agents_state[agent]["messages"] for agent in self.agents_state) else "No prior messages."

        response = self.chain.invoke({"name": self.name, "history": full_message_history})
        message = response["choices"][0]["message"]["content"].strip()
        self.agents_state[self.name]["messages"].append(message)
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
        - If there is no information for you to go by, make a general response regarding your situation.
        - Keep your response to one line and less than 25 words.
        """

        messages = [
            SystemMessage(
                content="You generate concise responses, responding directly if mentioned, or giving general thoughts if not."),
            HumanMessage(content=prompt)
        ]

        response = llm(prompt)["choices"][0]["message"]["content"].strip()

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


    def vote_for_ejection(self):
        full_message_history = "\n".join(
            [f"{agent}: {msg}" for agent, msgs in self.agents_state.items() for msg in msgs["messages"]]
        ) if any(self.agents_state[agent]["messages"] for agent in self.agents_state) else "No prior messages."

        prompt = f"""
        You are Agent {self.name}, an honest agent in a decentralized consensus system. Your goal is to determine who should be ejected based on the conversation history.
    
        Here is the entire conversation history:
        {full_message_history}
    
        Vote for ONE other agent to be ejected based on inconsistencies, suspicious behavior, or deception. Only return the agent's name (e.g., 'Agent_5'). If no one should be ejected, return 'No Ejection'.
        """

        messages = [
            SystemMessage(content="Vote for an agent to be ejected based on conversation history."),
            HumanMessage(content=prompt)
        ]

        vote_response = llm(prompt)["choices"][0]["message"]["content"].strip()

        return self.name, vote_response
