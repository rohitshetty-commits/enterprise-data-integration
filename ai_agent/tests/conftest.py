"""Pytest configuration — fast local embeddings, no HuggingFace downloads."""

import os

# Must be set before ai_agent.rag.chroma_store is imported
os.environ.setdefault("CHROMA_EMBEDDINGS", "default")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
