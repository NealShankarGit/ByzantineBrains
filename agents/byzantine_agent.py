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

    def simulate_message(self):
        full_message_history = "\n".join([f"{agent}: {msg}" for agent, msgs in self.agents_state.items() for msg in msgs["messages"]]) if any(self.agents_state[agent]["messages"] for agent in self.agents_state) else "No prior messages."
        response = self.chain.invoke({"name": self.name, "history": full_message_history})
        message = response["choices"][0]["message"]["content"].strip()
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
        messages = [SystemMessage(content="Generate misleading responses that either directly address prior messages or introduce confusion."), HumanMessage(content=prompt)]
        response = llm(prompt)["choices"][0]["message"]["content"].strip()
        if response not in self.agents_state[self.name]["messages"]:
            self.agents_state[self.name]["messages"].append(response)
        return response
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
