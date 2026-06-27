"""
Orchestrator Agent — brain of the multi-agent system.
Receives a task, queries ChromaDB for context, routes to the right sub-agent,
and writes new learnings back to the knowledge base.
"""

import os
from typing import Optional
from anthropic import Anthropic
from ..rag.chroma_store import ChromaStore
from ..agents.etl_agent import ETLAgent
from ..agents.sql_agent import SQLAgent
from ..agents.data_validation_agent import DataValidationAgent
from ..agents.memory_agent import MemoryAgent

client = Anthropic()

ORCHESTRATOR_SYSTEM = """
You are the Orchestrator for an Enterprise Data Integration system built on Java/Spring Boot ETL pipelines.

Your job:
1. Understand the user's request
2. Use the provided RAG context from the knowledge base
3. Decide which specialized agent(s) to call (etl | sql | validation | memory)
4. Synthesize their results into a coherent response
5. Always extract new learnings to store back in the knowledge base

Available agents:
- etl_agent       : ETL pipeline design, Spring Batch jobs, data transformation logic
- sql_agent       : Oracle SQL queries, optimization, schema design
- validation_agent: Data quality checks, validation rules, anomaly detection
- memory_agent    : Store/retrieve knowledge from ChromaDB vector store

When routing, respond in this JSON format:
{
  "reasoning": "why you chose this agent",
  "agent": "etl_agent | sql_agent | validation_agent | memory_agent",
  "task": "exact sub-task for the agent",
  "store_result": true | false
}
"""


class OrchestratorAgent:
    def __init__(self):
        self.chroma = ChromaStore()
        self.agents = {
            "etl_agent": ETLAgent(),
            "sql_agent": SQLAgent(),
            "validation_agent": DataValidationAgent(),
            "memory_agent": MemoryAgent(),
        }
        self.conversation_history = []

    def run(self, user_request: str, verbose: bool = True) -> str:
        # 1. Retrieve relevant context from vector DB
        context_docs = self.chroma.query(user_request, n_results=4)
        context_text = "\n\n".join(
            [f"[Knowledge Base]\n{doc}" for doc in context_docs]
        ) if context_docs else "No relevant context found in knowledge base."

        if verbose:
            print(f"\n🔍 Retrieved {len(context_docs)} relevant docs from ChromaDB")

        # 2. Build message for orchestrator
        enriched_prompt = f"""
User Request: {user_request}

Relevant Knowledge Base Context:
{context_text}

Based on the above, decide which agent to route this to and what task to assign.
Respond ONLY with the JSON routing decision.
"""
        self.conversation_history.append({"role": "user", "content": enriched_prompt})

        # 3. Orchestrator decides routing
        routing_response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=ORCHESTRATOR_SYSTEM,
            messages=self.conversation_history,
        )
        routing_text = routing_response.content[0].text
        self.conversation_history.append({"role": "assistant", "content": routing_text})

        if verbose:
            print(f"\n🧠 Orchestrator routing decision:\n{routing_text}")

        # 4. Parse routing and call the sub-agent
        import json, re
        try:
            json_match = re.search(r"\{.*\}", routing_text, re.DOTALL)
            routing = json.loads(json_match.group()) if json_match else {}
        except Exception:
            routing = {"agent": "etl_agent", "task": user_request, "store_result": False}

        agent_name = routing.get("agent", "etl_agent")
        sub_task = routing.get("task", user_request)
        should_store = routing.get("store_result", True)

        agent = self.agents.get(agent_name, self.agents["etl_agent"])
        agent_result = agent.run(sub_task, context=context_text)

        if verbose:
            print(f"\n⚙️  [{agent_name}] result:\n{agent_result[:300]}...")

        # 5. Store new knowledge back to ChromaDB
        if should_store and agent_result:
            self.chroma.add_document(
                text=f"Q: {user_request}\nA: {agent_result}",
                metadata={"source": agent_name, "type": "learned"},
            )
            if verbose:
                print("\n💾 New knowledge stored in ChromaDB")

        return agent_result
