"""
Cloud sync — ingest knowledge from GitHub repos and public URLs into ChromaDB.
"""

import hashlib
import os
import re
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import quote

import httpx

from .chroma_store import ChromaStore

GITHUB_API = "https://api.github.com"
DEFAULT_GITHUB_PATHS = ["README.md", "docs/"]


class CloudSyncService:
    def __init__(self, chroma: Optional[ChromaStore] = None):
        self.chroma = chroma or ChromaStore()
        self._last_sync: Optional[datetime] = None
        self._sync_counts: dict = {}

    def _github_headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _content_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _already_synced(self, origin_url: str) -> bool:
        """Check if origin_url exists in knowledge base metadata."""
        if self.chroma.count() == 0:
            return False
        try:
            results = self.chroma.collection.get(
                where={"origin_url": origin_url},
                include=["metadatas"],
            )
            return bool(results and results.get("ids"))
        except Exception:
            return False

    def _store_synced_doc(
        self,
        text: str,
        origin_url: str,
        source: str,
        extra_meta: Optional[dict] = None,
    ) -> bool:
        if self._already_synced(origin_url):
            return False
        meta = {
            "source": source,
            "type": "cloud_sync",
            "origin_url": origin_url,
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": self._content_hash(text),
        }
        if extra_meta:
            meta.update(extra_meta)
        self.chroma.add_document(text=text, metadata=meta)
        return True

    def sync_github_repo(
        self,
        owner: str,
        repo: str,
        paths: Optional[List[str]] = None,
    ) -> dict:
        """
        Sync files from a GitHub repository into ChromaDB.
        Fetches README.md and files under docs/ by default.
        """
        paths = paths or DEFAULT_GITHUB_PATHS
        added = 0
        skipped = 0
        errors: List[str] = []

        with httpx.Client(headers=self._github_headers(), timeout=30.0) as client:
            for path_pattern in paths:
                if path_pattern.endswith("/"):
                    added, skipped, errors = self._sync_github_dir(
                        client, owner, repo, path_pattern.strip("/"), added, skipped, errors
                    )
                else:
                    added, skipped, errors = self._sync_github_file(
                        client, owner, repo, path_pattern, added, skipped, errors
                    )

        self._last_sync = datetime.now(timezone.utc)
        self._sync_counts["github"] = added
        return {
            "source": "github",
            "owner": owner,
            "repo": repo,
            "added": added,
            "skipped": skipped,
            "errors": errors,
        }

    def _sync_github_file(
        self,
        client: httpx.Client,
        owner: str,
        repo: str,
        path: str,
        added: int,
        skipped: int,
        errors: List[str],
    ) -> tuple:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{quote(path)}"
        origin = f"https://github.com/{owner}/{repo}/blob/main/{path}"
        try:
            resp = client.get(url)
            if resp.status_code == 404:
                return added, skipped, errors
            if resp.status_code != 200:
                errors.append(f"{path}: HTTP {resp.status_code}")
                return added, skipped, errors
            data = resp.json()
            if data.get("type") != "file":
                return added, skipped, errors
            import base64
            content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            if self._store_synced_doc(content, origin, f"github:{owner}/{repo}", {"path": path}):
                added += 1
            else:
                skipped += 1
        except Exception as e:
            errors.append(f"{path}: {e}")
        return added, skipped, errors

    def _sync_github_dir(
        self,
        client: httpx.Client,
        owner: str,
        repo: str,
        dir_path: str,
        added: int,
        skipped: int,
        errors: List[str],
    ) -> tuple:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{quote(dir_path)}"
        try:
            resp = client.get(url)
            if resp.status_code == 404:
                return added, skipped, errors
            if resp.status_code != 200:
                errors.append(f"{dir_path}: HTTP {resp.status_code}")
                return added, skipped, errors
            items = resp.json()
            if not isinstance(items, list):
                return added, skipped, errors
            for item in items:
                if item.get("type") == "file" and self._is_text_file(item.get("name", "")):
                    sub_path = item["path"]
                    added, skipped, errors = self._sync_github_file(
                        client, owner, repo, sub_path, added, skipped, errors
                    )
                elif item.get("type") == "dir":
                    added, skipped, errors = self._sync_github_dir(
                        client, owner, repo, item["path"], added, skipped, errors
                    )
        except Exception as e:
            errors.append(f"{dir_path}: {e}")
        return added, skipped, errors

    def _is_text_file(self, name: str) -> bool:
        return bool(re.search(r"\.(md|txt|json|yaml|yml|sql|py|ts|tsx|js|jsx)$", name, re.I))

    def sync_urls(self, urls: List[str]) -> dict:
        """Fetch public URLs and ingest text content into ChromaDB."""
        added = 0
        skipped = 0
        errors: List[str] = []

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            for url in urls:
                try:
                    resp = client.get(url)
                    if resp.status_code != 200:
                        errors.append(f"{url}: HTTP {resp.status_code}")
                        continue
                    text = resp.text
                    if len(text.strip()) < 50:
                        skipped += 1
                        continue
                    if self._store_synced_doc(text[:50000], url, "url_sync", {"url": url}):
                        added += 1
                    else:
                        skipped += 1
                except Exception as e:
                    errors.append(f"{url}: {e}")

        self._last_sync = datetime.now(timezone.utc)
        self._sync_counts["urls"] = added
        return {"source": "urls", "added": added, "skipped": skipped, "errors": errors}

    def sync_all(self) -> dict:
        """Run enabled sync sources from environment."""
        if os.getenv("CLOUD_SYNC_ENABLED", "true").lower() != "true":
            return {"status": "disabled", "message": "CLOUD_SYNC_ENABLED is not true"}

        results = []
        sync_urls = os.getenv("SYNC_URLS", "")
        if sync_urls:
            urls = [u.strip() for u in sync_urls.split(",") if u.strip()]
            results.append(self.sync_urls(urls))

        sync_repo = os.getenv("SYNC_GITHUB_REPO", "")
        if sync_repo and "/" in sync_repo:
            owner, repo = sync_repo.split("/", 1)
            results.append(self.sync_github_repo(owner.strip(), repo.strip()))

        return {
            "status": "completed",
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "results": results,
            "kb_total": self.chroma.count(),
        }

    def status(self) -> dict:
        return {
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "sync_counts": self._sync_counts,
            "kb_total": self.chroma.count(),
            "cloud_sync_enabled": os.getenv("CLOUD_SYNC_ENABLED", "true"),
        }
