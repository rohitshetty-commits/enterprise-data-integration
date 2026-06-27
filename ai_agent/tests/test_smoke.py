"""
Smoke tests for the AI agent layer.
These run without making real API calls (mocked) to validate structure.
"""

import pytest
import os
import sys

# Ensure the package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

EXPECTED_AGENTS = {
    "interface_agent",
    "gotham_agent",
    "etl_agent",
    "sql_agent",
    "validation_agent",
    "memory_agent",
}


def test_chroma_store_init(tmp_path):
    """ChromaDB store initializes and can add/query documents."""
    os.environ["CHROMA_PATH"] = str(tmp_path / "test_db")
    from ai_agent.rag.chroma_store import ChromaStore
    store = ChromaStore()
    assert store.count() == 0

    doc_id = store.add_document("Spring Batch ItemReader pattern for Oracle", {"source": "test"})
    assert doc_id is not None
    assert store.count() == 1

    results = store.query("Spring Batch")
    assert len(results) == 1
    assert "Spring Batch" in results[0]


def test_chroma_batch_ingest(tmp_path):
    """ChromaDB can batch ingest multiple documents."""
    os.environ["CHROMA_PATH"] = str(tmp_path / "test_db2")
    from ai_agent.rag.chroma_store import ChromaStore
    store = ChromaStore()
    texts = ["Oracle SQL tuning", "SCD Type 2 MERGE pattern", "FDMEE batch load"]
    ids = store.add_documents(texts)
    assert len(ids) == 3
    assert store.count() == 3


def test_fastapi_app_starts():
    """FastAPI app object is created without errors."""
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
    os.environ["CHROMA_PATH"] = "/tmp/test_chroma_smoke"
    from ai_agent.api.main import app
    assert app is not None
    assert app.title == "Enterprise ETL AI Orchestrator"


@pytest.mark.asyncio
async def test_health_endpoint(tmp_path):
    """Health endpoint returns expected structure and all agents."""
    from httpx import AsyncClient, ASGITransport
    os.environ["CHROMA_PATH"] = str(tmp_path / "health_db")
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
    from ai_agent.api.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "kb_docs" in data
    assert "agents" in data
    assert set(data["agents"]) == EXPECTED_AGENTS


def test_orchestrator_has_all_agents(tmp_path):
    """Orchestrator registers Interface, Gotham, and ETL agents."""
    os.environ["CHROMA_PATH"] = str(tmp_path / "orch_db")
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
    from ai_agent.orchestrator.orchestrator import OrchestratorAgent
    orch = OrchestratorAgent()
    assert set(orch.agents.keys()) == EXPECTED_AGENTS


def test_interface_and_gotham_agents_import():
    """New specialist agents can be instantiated."""
    from ai_agent.agents.interface_agent import InterfaceAgent
    from ai_agent.agents.gotham_agent import GothamAgent
    assert InterfaceAgent().history == []
    assert GothamAgent().history == []
