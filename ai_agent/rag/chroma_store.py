"""
ChromaDB Vector Store — the persistent knowledge base for all agents.
Stores ETL patterns, SQL snippets, validation rules, and learned Q&As.
New data ingested here is immediately available to all agents via RAG.
"""

import chromadb
from chromadb.utils import embedding_functions
from typing import List, Optional
import uuid
import os


CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION_NAME = "enterprise_etl_knowledge"

# Uses sentence-transformers locally — no API key needed
EMBED_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


class ChromaStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=EMBED_FN,
            metadata={"hnsw:space": "cosine"},
        )
        print(f"✅ ChromaDB loaded: {self.collection.count()} documents in knowledge base")

    def add_document(self, text: str, metadata: Optional[dict] = None) -> str:
        """Add a single document to the knowledge base."""
        doc_id = str(uuid.uuid4())
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id],
        )
        return doc_id

    def add_documents(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> List[str]:
        """Batch add multiple documents."""
        ids = [str(uuid.uuid4()) for _ in texts]
        self.collection.add(
            documents=texts,
            metadatas=metadatas or [{} for _ in texts],
            ids=ids,
        )
        print(f"💾 Added {len(texts)} documents to knowledge base")
        return ids

    def query(self, query_text: str, n_results: int = 4, where: Optional[dict] = None) -> List[str]:
        """Query the knowledge base for relevant documents."""
        kwargs = {
            "query_texts": [query_text],
            "n_results": min(n_results, max(self.collection.count(), 1)),
        }
        if where:
            kwargs["where"] = where
        results = self.collection.query(**kwargs)
        return results["documents"][0] if results["documents"] else []

    def query_with_metadata(self, query_text: str, n_results: int = 4) -> List[dict]:
        """Query and return docs with their metadata."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, max(self.collection.count(), 1)),
            include=["documents", "metadatas", "distances"],
        )
        items = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            items.append({"document": doc, "metadata": meta, "similarity": 1 - dist})
        return items

    def ingest_file(self, filepath: str, chunk_size: int = 500) -> int:
        """Ingest a text file into the knowledge base in chunks."""
        with open(filepath, "r") as f:
            content = f.read()
        # Chunk by paragraphs first, then by size
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        chunks = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) < chunk_size:
                current += "\n\n" + para
            else:
                if current:
                    chunks.append(current.strip())
                current = para
        if current:
            chunks.append(current.strip())

        source_name = os.path.basename(filepath)
        metadatas = [{"source": source_name, "type": "ingested_file"} for _ in chunks]
        self.add_documents(chunks, metadatas)
        print(f"📄 Ingested '{source_name}' → {len(chunks)} chunks added")
        return len(chunks)

    def count(self) -> int:
        return self.collection.count()

    def reset(self):
        """Wipe the collection — use with caution."""
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=EMBED_FN,
        )
        print("⚠️  Knowledge base reset.")
