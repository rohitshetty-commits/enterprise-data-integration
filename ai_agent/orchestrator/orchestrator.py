"""
Orchestrator Agent — brain of the multi-agent system.
Receives a task, queries ChromaDB for context, routes to the right sub-agent,
and writes new learnings back to the knowledge base.
"""

import json
import re
from anthropic import Anthropic
from ..rag.chroma_store import ChromaStore
from ..agents.etl_agent import ETLAgent
from ..agents.sql_agent import SQLAgent
from ..agents.data_validation_agent import DataValidationAgent
from ..agents.memory_agent import MemoryAgent
from ..agents.interface_agent import InterfaceAgent
from ..agents.gotham_agent import GothamAgent

client = Anthropic()

ORCHESTRATOR_SYSTEM = """
You are the Orchestrator for an Enterprise Data Integration and App Building platform.

Your job:
1. Understand the user's request
2. Use the provided RAG context from the knowledge base
3. Decide which specialized agent(s) to call
4. For full-stack features, route sequentially: Gotham (API/schema) first, then Interface (UI)
5. Synthesize results into a coherent response
6. Extract new learnings to store back in the knowledge base

Available agents:
- interface_agent   : React/Next.js UI, components, styling, forms, client state, browser API calls
- gotham_agent      : FastAPI backend, SQL, schema, architecture, APIs, security, deployment
- etl_agent         : ETL pipeline design, Spring Batch jobs, data transformation logic
- sql_agent         : Oracle SQL queries, optimization, schema design (ETL-focused)
- validation_agent  : Data quality checks, validation rules, anomaly detection
- memory_agent      : Store/retrieve knowledge from ChromaDB vector store

Routing rules:
- UI, React, Next.js, component, page, CSS, frontend → interface_agent
- API, FastAPI, backend, SQL schema, architecture, database → gotham_agent
- Spring Batch, ETL pipeline, delta load, FDMEE, HFM → etl_agent
- Oracle SQL tuning, PL/SQL, ETL queries → sql_agent
- Data quality, validation rules, reconciliation → validation_agent
- Store, remember, retrieve knowledge → memory_agent
- Full-stack feature (e.g. registration page + API) → gotham_agent first, follow_up interface_agent

When routing, respond in this JSON format only:
{
  "reasoning": "why you chose this agent",
  "agent": "interface_agent | gotham_agent | etl_agent | sql_agent | validation_agent | memory_agent",
  "task": "exact sub-task for the agent",
  "store_result": true,
  "follow_up_agent": null,
  "follow_up_task": null
}

Set follow_up_agent and follow_up_task when a second agent should run after the first (e.g. API then UI).
"""


def _infer_agent_from_keywords(user_request: str) -> str:
    """Fallback routing when JSON parsing fails."""
    text = user_request.lower()
    ui_keywords = ("react", "next.js", "nextjs", "frontend", "ui", "component", "page", "css", "tailwind", "browser")
    backend_keywords = ("fastapi", "backend", "api route", "schema", "migration", "architecture", "postgresql", "database design")
    if any(k in text for k in ui_keywords):
        return "interface_agent"
    if any(k in text for k in backend_keywords):
        return "gotham_agent"
    return "gotham_agent"


class OrchestratorAgent:
    def __init__(self):
        self.chroma = ChromaStore()
        self.agents = {
            "interface_agent": InterfaceAgent(),
            "gotham_agent": GothamAgent(),
            "etl_agent": ETLAgent(),
            "sql_agent": SQLAgent(),
            "validation_agent": DataValidationAgent(),
            "memory_agent": MemoryAgent(),
        }
        self.conversation_history = []

    def _parse_routing(self, routing_text: str, user_request: str) -> dict:
        try:
            json_match = re.search(r"\{.*\}", routing_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        fallback = _infer_agent_from_keywords(user_request)
        return {"agent": fallback, "task": user_request, "store_result": True}

    def _run_agent(self, agent_name: str, task: str, context_text: str, verbose: bool) -> str:
        agent = self.agents.get(agent_name)
        if not agent:
            agent = self.agents["gotham_agent"]
            agent_name = "gotham_agent"
        result = agent.run(task, context=context_text)
        if verbose:
            preview = result[:300] + ("..." if len(result) > 300 else "")
            print(f"\n⚙️  [{agent_name}] result:\n{preview}")
        return result

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

        routing = self._parse_routing(routing_text, user_request)
        agent_name = routing.get("agent", "gotham_agent")
        sub_task = routing.get("task", user_request)
        should_store = routing.get("store_result", True)
        follow_up_agent = routing.get("follow_up_agent")
        follow_up_task = routing.get("follow_up_task")

        # 4. Run primary agent
        agent_result = self._run_agent(agent_name, sub_task, context_text, verbose)

        # 5. Optional follow-up agent (e.g. Gotham then Interface)
        follow_up_result = ""
        if follow_up_agent and follow_up_task:
            combined_context = f"{context_text}\n\n[Prior agent ({agent_name}) output]\n{agent_result}"
            follow_up_result = self._run_agent(
                follow_up_agent, follow_up_task, combined_context, verbose
            )
            agent_result = f"{agent_result}\n\n---\n\n{follow_up_result}"

        # 6. Store new knowledge back to ChromaDB
        if should_store and agent_result:
            self.chroma.add_document(
                text=f"Q: {user_request}\nA: {agent_result}",
                metadata={"source": agent_name, "type": "learned"},
            )
            if verbose:
                print("\n💾 New knowledge stored in ChromaDB")

        return agent_result
