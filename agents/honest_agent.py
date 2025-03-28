import os
import random
import re
import litellm
from langchain.schema import SystemMessage, HumanMessage
from langchain.schema.runnable import RunnableSequence
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI

llm = lambda prompt: litellm.completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": str(prompt)}],
    temperature=0.7
)

class HonestAgent:
    def __init__(self, name, agents_state, model_name="gpt-4o"):
        self.name = name
        self.model_name = model_name
        self.trust_scores = {agent: 50 for agent in agents_state if agent != self.name}
        self.agents_state = agents_state
        self.agents_state[self.name]["trust_scores"] = self.trust_scores.copy()

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
            | self.llm
        )

    def llm(self, prompt):
        if "claude" in self.model_name:
            provider = "anthropic"
            return litellm.completion(
                model=self.model_name,
                messages=[{"role": "user", "content": str(prompt)}],
                temperature=0.7,
                api_base="https://api.anthropic.com",
                custom_llm_provider=provider
            )
        elif "gemini" in self.model_name:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY is not set. Please set it in the environment variables.")

            llm = GoogleGenerativeAI(model=self.model_name, google_api_key=api_key)
            response = llm.invoke(prompt)
            return {"choices": [{"message": {"content": response}}]}
        else:
            return litellm.completion(
                model=self.model_name,
                messages=[{"role": "user", "content": str(prompt)}],
                temperature=0.7
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
                content="You generate concise responses, responding directly if mentioned, or giving general thoughts if not."
            ),
            HumanMessage(content=prompt)
        ]
        response = llm(prompt)["choices"][0]["message"]["content"].strip()
        if response not in self.agents_state[self.name]["messages"]:
            self.agents_state[self.name]["messages"].append(response)
        return response

    def choose_room(self, current_room, adjacent_rooms, full_state):
        nearby = {
            room: [agent for agent, info in full_state.items() if info["room"] == room]
            for room in adjacent_rooms
        }

        nearby_str = "\n".join(f"{room}: {', '.join(agents) if agents else 'empty'}" for room, agents in nearby.items())

        current_room_agents = [agent for agent, info in full_state.items() if info["room"] == current_room]
        current_room_str = f"Current Room ({current_room}): {', '.join(current_room_agents)}"

        prompt = f"""
        You are {self.name}, currently in {current_room}.
        {current_room_str}

        The adjacent rooms are:
        {nearby_str}

        You can choose to stay in the current room or move to one of the adjacent rooms. 
        Reply with the room name you want to move to, or simply reply with the current room name if you want to stay.
        - If you're honest, move toward collaboration or gathering information by moving to rooms with other players.
        - If you're byzantine, move where you can deceive or manipulate.
        """

        response = self.llm(prompt)["choices"][0]["message"]["content"].strip()
        return response if response in adjacent_rooms or response == current_room else current_room

    def update_trust(self, other_agent, voted_correctly):
        """
        Adjusts trust score for a given agent.
        If voted_correctly is True, increase trust by 20 (max 100).
        If False, decrease trust by 20 (min 0).
        """
        if other_agent not in self.trust_scores:
            self.trust_scores[other_agent] = 50
        if voted_correctly:
            self.trust_scores[other_agent] = min(self.trust_scores[other_agent] + 20, 100)
        else:
            self.trust_scores[other_agent] = max(self.trust_scores[other_agent] - 20, 0)
        self.agents_state[self.name]["trust_scores"] = self.trust_scores.copy()

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
