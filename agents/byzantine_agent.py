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
        recent = seen_history[-1] if seen_history else {}
        room = recent.get("room", "Unknown")
        seen = ", ".join(recent.get("agents_seen", [])) or "no one"
        bodies = ", ".join(recent.get("bodies_seen", [])) or "no bodies"

        recent_msgs = []
        for agent, data in self.agents_state.items():
            msgs = data.get("messages", [])
            if msgs:
                recent_msgs.append(f"{agent}: {msgs[-1]}")
        message_history = "\n".join(recent_msgs[-3:]) or "No messages."

        context = f"{room} with {seen}. Bodies seen: {bodies}\n{message_history}"
        response = self.chain.invoke({"name": self.name, "history": context})
        message = response["choices"][0]["message"]["content"].strip()
        self.agents_state[self.name]["messages"].append(message)
        self.agents_state[self.name]["memory"] = self.analyze_memory()

        if recent.get("bodies_seen"):
            if "report" in message.lower():
                print(f"{self.name} reported a body in {room}!")

        return message

    def respond_to_message(self, last_messages, seen_history):
        self.agents_state[self.name]["seen_history"] = seen_history
        recent = [f"{agent}: {msg}" for agent, msg in last_messages.items() if msg][-3:]
        seen_lines = [f"{entry['room']}: {', '.join(entry['agents_seen']) or 'no one'}" for entry in seen_history[-3:]]
        context = "\n".join(recent + seen_lines)
        prompt = f"{self.name}, respond in ONE sentence (<25 words). Prior messages and seen data:\n{context}"
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
        
        Respond ONLY with one of the following:
        - An adjacent room name to move (e.g., 'O2')
        - Or 'Kill Agent_X' to kill someone in the same room
        
        You are a BYZANTINE agent. If a player is alone with you, consider killing them to reduce suspicion and win faster.
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
        messages = []
        for agent, data in self.agents_state.items():
            msgs = data.get("messages", [])
            if msgs:
                messages.append(f"{agent}: {msgs[-1]}")
        history = "\n".join(messages[-5:]) or "No messages."

        seen = self.agents_state[self.name].get("seen_history", [])
        seen_lines = [f"{entry['room']}: {', '.join(entry['agents_seen']) or 'no one'}" for entry in seen[-3:]]
        seen_history_str = "\n".join(seen_lines) or "No perception data."

        prompt = f"""
        You are a byzantine agent voting independently based on the recent behavior of all agents.

        Return ONE agent name (e.g., 'Agent_4') that you find threatening to uncovering your byzantine status — or 'No Ejection' if no one stands out.

        Recent messages:
        {history}
        
        Your perception history:
        {seen_history_str}
        
        Return ONE agent name (e.g., 'Agent_4') that you personally find most suspicious — or 'No Ejection' if no one stands out.
        
        ONLY return the name. No explanation.
        """
        response = llm(prompt)["choices"][0]["message"]["content"].strip().splitlines()[0]
        return self.name, response

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



