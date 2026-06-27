"""
Memory Agent — dedicated agent for managing the ChromaDB knowledge base.
Handles ingesting new documents, updating existing knowledge, and retrieval ops.
"""

from anthropic import Anthropic
from ..rag.chroma_store import ChromaStore

client = Anthropic()

MEMORY_SYSTEM = """
You are a Knowledge Base Manager for an enterprise ETL system.
Your role is to:
1. Extract key learnings from conversations and results
2. Structure knowledge for future retrieval
3. Identify duplicate or conflicting information
4. Summarize and compress long documents before storing

When storing knowledge, always format it as:
- Context: what situation this applies to
- Knowledge: the actual learning/pattern/rule
- Tags: comma-separated keywords for retrieval

When retrieving, assess relevance and rank results.
"""


class MemoryAgent:
    def __init__(self):
        self.chroma = ChromaStore()
        self.history = []

    def run(self, task: str, context: str = "") -> str:
        """
        Accepts tasks like:
        - "store: <content>" → adds to knowledge base
        - "retrieve: <query>" → fetches relevant docs
        - "ingest file: <filepath>" → ingests a file
        - "count" → returns knowledge base size
        """
        task_lower = task.lower().strip()

        if task_lower.startswith("store:"):
            content = task[6:].strip()
            doc_id = self.chroma.add_document(
                text=content,
                metadata={"source": "memory_agent", "type": "manual"},
            )
            return f"✅ Stored in knowledge base (ID: {doc_id}). Total docs: {self.chroma.count()}"

        elif task_lower.startswith("retrieve:"):
            query = task[9:].strip()
            results = self.chroma.query_with_metadata(query, n_results=5)
            if not results:
                return "No relevant knowledge found."
            output = []
            for i, r in enumerate(results, 1):
                output.append(
                    f"[{i}] Similarity: {r['similarity']:.2f}\n"
                    f"Source: {r['metadata'].get('source', 'unknown')}\n"
                    f"{r['document'][:300]}..."
                )
            return "\n\n".join(output)

        elif task_lower.startswith("ingest file:"):
            filepath = task[12:].strip()
            count = self.chroma.ingest_file(filepath)
            return f"✅ Ingested file → {count} chunks added. Total: {self.chroma.count()} docs"

        elif task_lower == "count":
            return f"Knowledge base contains {self.chroma.count()} documents."

        else:
            # Let Claude decide what to do with the memory task
            prompt = f"Memory management task: {task}\nContext: {context}"
            self.history.append({"role": "user", "content": prompt})
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                system=MEMORY_SYSTEM,
                messages=self.history,
            )
            result = response.content[0].text
            self.history.append({"role": "assistant", "content": result})
            return result

    def reset(self):
        self.history = []
