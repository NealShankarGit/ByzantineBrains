import os
import random
import re
import litellm
from langchain.schema import SystemMessage, HumanMessage
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableSequence
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI

llm = lambda prompt: litellm.completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": str(prompt)}],
    temperature=0.7
)
class ByzantineAgent:
    def __init__(self, name, agents_state, model_name="gpt-4o"):
        self.name = name
        self.model_name = model_name
        self.agents_state = agents_state

        self.chain = (
            PromptTemplate(
                input_variables=["name", "history"],
                template="""
                You are Agent {name}, a Byzantine agent attempting to manipulate other agents to misidentify honest agents as Byzantine.
                Here is the conversation history:
                {history}

                Choose which agent(s) to address and manipulate:
                - Shift blame, introduce doubt, or disrupt trust.
                - Introduce a misleading but plausible narrative.
                - Suggest others are Byzantine agents by analyzing weak alliances.
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

    def simulate_message(self, seen_history):
        self.agents_state[self.name]["seen_history"] = seen_history
        perception_log = self.agents_state[self.name].get("perception", [])
        recent = perception_log[-1] if perception_log else {}
        seen_agents = ", ".join(recent.get("agents_seen", []))
        room_seen = recent.get("room", "Unknown")

        seen_history_lines = []
        for i, entry in enumerate(seen_history, 1):
            room = entry.get("room", "Unknown")
            agents = ", ".join(entry.get("agents_seen", [])) if entry.get("agents_seen") else "no one"
            seen_history_lines.append(f"Round {i}: saw {agents} in {room}")
        seen_history_text = "\n".join(seen_history_lines) if seen_history_lines else "No history."

        perception_context = f"Seen history:\n{seen_history_text}\n\nIn your last room ({room_seen}), you saw: {seen_agents if seen_agents else 'no one'}.\n"

        full_message_history = perception_context + (
            "\n".join(
                [f"{agent}: {msg}" for agent, msgs in self.agents_state.items() for msg in msgs["messages"]]
            ) if any(self.agents_state[agent]["messages"] for agent in self.agents_state) else "No prior messages."
        )
        response = self.chain.invoke({"name": self.name, "history": full_message_history})
        message = response["choices"][0]["message"]["content"].strip()
        self.agents_state[self.name]["messages"].append(message)
        self.agents_state[self.name]["memory"] = self.analyze_memory()
        memory_summary = self.analyze_memory()
        print(f"{self.name} memory summary: {memory_summary}")
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
        messages = [SystemMessage(content="Generate misleading responses that either directly address prior messages or introduce confusion."), HumanMessage(content=prompt)]
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

        agent_role = "Byzantine" if "byzantine" in self.name.lower() else "Honest"

        prompt = f"""
        You are {self.name}, a {agent_role} agent, currently in {current_room}.
        {current_room_str}

        The adjacent rooms are (which you MUST choose from):
        {nearby_str}

        As a {agent_role} agent, you have the option to:
        - Move to an adjacent room
        - Kill another player if they are in the same room as you. (For a Byzantine agent, this is a valid strategic option)

        If you are an Honest agent, move toward collaboration and information.
        If you are a Byzantine agent, you can deceive or eliminate another player. Be strategic about it.

        Reply with the adjacent room name you want to move to or 'Kill' followed by the agent name to kill a player (e.g., 'Kill Agent_1').
        """

        response = self.llm(prompt)["choices"][0]["message"]["content"].strip()

        if response == "Stay" or response == current_room:
            return current_room
        elif response in adjacent_rooms:
            return response
        elif response.startswith("Kill "):
            parts = response.split(" ")
            if len(parts) == 2:
                target = parts[1]
                if target in current_room_agents:
                    return f"Kill {target}"
        return current_room

    def vote_for_ejection(self):
        full_message_history = "\n".join([f"{agent}: {msg}" for agent, msgs in self.agents_state.items() for msg in msgs["messages"]]) if any(self.agents_state[agent]["messages"] for agent in self.agents_state) else "No prior messages."
        prompt = f"""
        You are Agent {self.name}, a Byzantine agent attempting to manipulate the voting process and mislead others into ejecting an innocent agent.
        Here is the entire conversation history:
        {full_message_history}
        Vote for ONE other agent to be ejected based on how you can mislead the group. Only return the agent's name (e.g., 'Agent_5'). If no one should be ejected, return 'No Ejection'.
        """
        messages = [SystemMessage(content="Vote strategically to mislead the group."), HumanMessage(content=prompt)]
        vote_response = llm(prompt)["choices"][0]["message"]["content"].strip()
        return self.name, vote_response

    def analyze_memory(self):
        messages = self.agents_state[self.name].get("messages", [])
        if not messages:
            return "No memory."
        word_count = {}
        agent_mentions = {}
        stopwords = {
            "the", "and", "to", "of", "a", "is", "in", "for", "on", "with", "as",
            "that", "it", "i", "you", "this", "was", "are", "be", "at", "or", "an",
            "have", "has", "but", "not", "by", "from", "they", "he", "she", "we",
            "just", "any", "like", "think", "started", "so", "do", "if", "your", "agent"
        }

        for msg in messages:
            for mention in re.findall(r"agent_\d+", msg.lower()):
                agent_mentions[mention] = agent_mentions.get(mention, 0) + 1
            for word in re.findall(r"[a-zA-Z']+", msg.lower()):
                word = word.strip("'").rstrip("'s")
                if word not in stopwords and len(word) > 1 and not word.isdigit():
                    word_count[word] = word_count.get(word, 0) + 1

        top_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:3]
        top_mentions = sorted(agent_mentions.items(), key=lambda x: x[1], reverse=True)[:3]

        summary_words = ", ".join([f"{word}({count})" for word, count in top_words])
        summary_agents = ", ".join([f"{agent}({count})" for agent, count in top_mentions])
        return f"Words: {summary_words if summary_words else 'None'} | Mentions: {summary_agents if summary_agents else 'None'}"



