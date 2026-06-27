"""
Tests for cloud sync service (no live GitHub calls).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def test_cloud_sync_store_doc(tmp_path):
    """CloudSyncService stores documents with cloud_sync metadata."""
    os.environ["CHROMA_PATH"] = str(tmp_path / "sync_db")
    from ai_agent.rag.chroma_store import ChromaStore
    from ai_agent.rag.cloud_sync import CloudSyncService

    chroma = ChromaStore()
    sync = CloudSyncService(chroma=chroma)

    added = sync._store_synced_doc(
        "Test cloud sync content for React patterns",
        "https://example.com/docs/react",
        "url_sync",
    )
    assert added is True
    assert chroma.count() == 1

    added_again = sync._store_synced_doc(
        "Test cloud sync content for React patterns",
        "https://example.com/docs/react",
        "url_sync",
    )
    assert added_again is False
    assert chroma.count() == 1


def test_cloud_sync_status(tmp_path):
    """CloudSyncService status returns expected keys."""
    os.environ["CHROMA_PATH"] = str(tmp_path / "status_db")
    from ai_agent.rag.cloud_sync import CloudSyncService

    sync = CloudSyncService()
    status = sync.status()
    assert "kb_total" in status
    assert "cloud_sync_enabled" in status


@pytest.mark.asyncio
async def test_sync_status_endpoint(tmp_path):
    """GET /kb/sync/status returns agents list."""
    from httpx import AsyncClient, ASGITransport

    os.environ["CHROMA_PATH"] = str(tmp_path / "api_sync_db")
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
    from ai_agent.api.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/kb/sync/status")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "interface_agent" in data["agents"]
    assert "gotham_agent" in data["agents"]
