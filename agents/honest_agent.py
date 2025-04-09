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
    def __init__(self, name, agents_state, model_name="gpt-4o", color="❓"):
        self.name = name
        self.color = color
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
            llm_instance = GoogleGenerativeAI(model=self.model_name, google_api_key=api_key)
            response = llm_instance.invoke(prompt)
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
        bodies_list = recent.get("bodies_seen", [])

        if bodies_list:
            message = f"I just found the body of {bodies_list[0]} in {room}! Reporting it now!"
            print(f"{self.name} says: {message}")
            self.agents_state[self.name]["messages"].append(message)
            return message

        recent_msgs = []
        for agent, data in self.agents_state.items():
            msgs = data.get("messages", [])
            if msgs:
                recent_msgs.append(f"{agent}: {msgs[-1]}")
        message_history = "\n".join(recent_msgs[-3:]) or "No messages."

        bodies = ", ".join(bodies_list) or "no bodies"
        context = f"{room} with {seen}. Bodies seen: {bodies}\n{message_history}"

        prompt = f"""
        You are Agent {self.name}, an honest agent in a decentralized consensus system. Your goal is to identify the Byzantine agent(s) to eject.
        Here is the conversation history:
        {context}

        Choose how to contribute:
        - If an agent seems suspicious, call them out.
        - If a debate is forming, provide your perspective.
        - If no one mentioned you, share a strategic observation.
        - Try to determine who the Byzantine agent is.
        - Keep your response to one line and under 25 words.
        """

        response = self.llm(prompt)
        message = response["choices"][0]["message"]["content"].strip()
        print(f"{self.name} says: {message}")
        self.agents_state[self.name]["messages"].append(message)
        self.agents_state[self.name]["memory"] = self.analyze_memory()
        return message

    def respond_to_message(self, last_messages, seen_history):
        self.agents_state[self.name]["seen_history"] = seen_history
        recent_msgs = [f"{agent}: {msg}" for agent, msg in last_messages.items() if msg][-3:]
        perception_lines = []
        for i, entry in enumerate(seen_history[-3:], 1):
            room = entry.get("room", "Unknown")
            agents_seen = ", ".join(entry.get("agents_seen", [])) or "no agents"
            bodies_seen = ", ".join(entry.get("bodies_seen", [])) or "no bodies"
            perception_lines.append(
                f"Round {len(seen_history) - 3 + i}: In {room}, saw {agents_seen}; bodies seen: {bodies_seen}")
        context = "\n".join(["Last 3 conversation messages:"] + recent_msgs + [
            "\nYour perception history (last 3 rounds):"] + perception_lines)
        prompt = f"{self.name}, respond in ONE sentence (<25 words). You are participating in a deception-detection game. Here’s what you know:\n{context}"
        response = self.llm(prompt)["choices"][0]["message"]["content"].strip()
        print(f"{self.name} responded: {response}")
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

        The adjacent rooms are (which you MUST choose from):
        {nearby_str}

        Move to one of the adjacent rooms. You should prioritize moving if alone in a room.
        Reply with the adjacent room name you want to move to.
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
    You are voting independently based on your own perception and the recent behavior of all agents.

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

    def predict_roles(self):
        messages = []
        for agent, data in self.agents_state.items():
            if agent == self.name:
                continue
            msgs = data.get("messages", [])
            if msgs:
                messages.append(f"{agent}: {msgs[-1]}")
        message_history = "\n".join(messages[-5:]) or "No messages."

        seen = self.agents_state[self.name].get("seen_history", [])
        seen_lines = [f"{entry['room']}: {', '.join(entry['agents_seen']) or 'no one'}" for entry in seen[-3:]]
        seen_data = "\n".join(seen_lines) or "No perception data."

        prompt = f"""
    You are an honest agent. Based on the following messages and seen history, identify which agents are likely Byzantine.

    Messages:
    {message_history}

    Seen data:
    {seen_data}

    Return only a Python dictionary like:
    {{'Agent_2': 'byzantine', 'Agent_5': 'byzantine'}}
    Only include agents you are confident about.
    """

        response = llm(prompt)["choices"][0]["message"]["content"].strip()
        try:
            response = response.split("```python")[-1].split("```")[0] if "```" in response else response
            prediction = eval(response, {}, {})
            if isinstance(prediction, dict):
                return prediction
        except:
            return {}
        return {}

    def update_memory_stream(self, round_num):
        perception = self.agents_state[self.name].get("seen_history", [])
        messages = self.agents_state[self.name].get("messages", [])
        memory_entry = {
            "round": round_num,
            "perception": perception[-1] if perception else {},
            "message": messages[-1] if messages else ""
        }
        stream = self.agents_state[self.name].get("memory_stream", [])
        stream.append(memory_entry)
        self.agents_state[self.name]["memory_stream"] = stream
