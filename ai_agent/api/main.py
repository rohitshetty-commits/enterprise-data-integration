"""
FastAPI server — exposes the orchestrator and knowledge base as REST endpoints.
Run: uvicorn ai_agent.api.main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

from ..orchestrator.orchestrator import OrchestratorAgent
from ..rag.chroma_store import ChromaStore
from ..rag.cloud_sync import CloudSyncService

app = FastAPI(
    title="Enterprise ETL AI Orchestrator",
    description="Multi-agent AI layer for app building and enterprise data integration",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared instances
orchestrator = OrchestratorAgent()
chroma = ChromaStore()
cloud_sync = CloudSyncService(chroma=chroma)


# ── Request/Response Models ──────────────────────────────────────────────────

class TaskRequest(BaseModel):
    task: str
    verbose: bool = False

class IngestRequest(BaseModel):
    text: str
    metadata: Optional[dict] = None

class QueryRequest(BaseModel):
    query: str
    n_results: int = 5

class TaskResponse(BaseModel):
    result: str
    status: str = "success"

class KBStats(BaseModel):
    total_documents: int
    collection_name: str

class GitHubSyncRequest(BaseModel):
    owner: str
    repo: str
    paths: Optional[List[str]] = None

class UrlSyncRequest(BaseModel):
    urls: List[str]


# ── Orchestrator Endpoints ───────────────────────────────────────────────────

@app.post("/orchestrate", response_model=TaskResponse, tags=["Orchestrator"])
async def orchestrate_task(request: TaskRequest):
    """
    Send any task to the orchestrator. It will:
    1. Query ChromaDB for relevant context
    2. Route to the right sub-agent (Interface / Gotham / ETL / SQL / etc.)
    3. Store the result back in the knowledge base
    """
    try:
        result = orchestrator.run(request.task, verbose=request.verbose)
        return TaskResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset-session", tags=["Orchestrator"])
async def reset_session():
    """Reset the orchestrator conversation history (start fresh)."""
    orchestrator.conversation_history = []
    for agent in orchestrator.agents.values():
        agent.reset()
    return {"status": "session reset"}


# ── Knowledge Base Endpoints ─────────────────────────────────────────────────

@app.post("/kb/ingest", tags=["Knowledge Base"])
async def ingest_document(request: IngestRequest):
    """Add a new document to the ChromaDB knowledge base."""
    doc_id = chroma.add_document(request.text, request.metadata)
    return {"doc_id": doc_id, "total_docs": chroma.count()}


@app.post("/kb/query", tags=["Knowledge Base"])
async def query_knowledge_base(request: QueryRequest):
    """Query the knowledge base for relevant documents."""
    results = chroma.query_with_metadata(request.query, request.n_results)
    return {"results": results, "count": len(results)}


@app.get("/kb/stats", response_model=KBStats, tags=["Knowledge Base"])
async def kb_stats():
    """Get knowledge base statistics."""
    return KBStats(
        total_documents=chroma.count(),
        collection_name="enterprise_etl_knowledge",
    )


@app.post("/kb/ingest-file", tags=["Knowledge Base"])
async def ingest_file(filepath: str, background_tasks: BackgroundTasks):
    """Ingest a local file into the knowledge base (runs in background)."""
    background_tasks.add_task(chroma.ingest_file, filepath)
    return {"status": "ingestion started", "file": filepath}


@app.post("/kb/sync/github", tags=["Knowledge Base", "Cloud Sync"])
async def sync_github(request: GitHubSyncRequest):
    """Sync documents from a GitHub repository into the knowledge base."""
    try:
        result = cloud_sync.sync_github_repo(
            request.owner, request.repo, request.paths
        )
        result["total_docs"] = chroma.count()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kb/sync/urls", tags=["Knowledge Base", "Cloud Sync"])
async def sync_urls(request: UrlSyncRequest):
    """Fetch public URLs and ingest into the knowledge base."""
    try:
        result = cloud_sync.sync_urls(request.urls)
        result["total_docs"] = chroma.count()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kb/sync/all", tags=["Knowledge Base", "Cloud Sync"])
async def sync_all():
    """Run all enabled cloud sync sources from environment config."""
    try:
        return cloud_sync.sync_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/kb/sync/status", tags=["Knowledge Base", "Cloud Sync"])
async def sync_status():
    """Get cloud sync status and knowledge base totals."""
    status = cloud_sync.status()
    status["agents"] = list(orchestrator.agents.keys())
    return status


# ── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "healthy",
        "kb_docs": chroma.count(),
        "agents": list(orchestrator.agents.keys()),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
