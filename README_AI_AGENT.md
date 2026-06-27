# AI Agent Layer — App Builder + Enterprise Data Integration

A Python multi-agent orchestration layer for **building full-stack apps** (React/Next.js + FastAPI) and **enterprise ETL** (Spring Batch, Oracle).  
Uses **Claude (claude-sonnet-4-6)** + **ChromaDB RAG** + **Ruflo** + **cloud sync** for a self-learning AI brain.

---

## Architecture

```
User / API Request
        ↓
 OrchestratorAgent  ←──── ChromaDB (RAG)  ←──── Cloud Sync (GitHub, URLs)
   ↙  ↓  ↓  ↘  ↘  ↘
Interface Gotham ETL SQL Validation Memory
(React)  (FastAPI)
        ↓
 FastAPI Orchestration API  (port 8000)
        ↓
 app/frontend (3000) + app/backend (8001)   ← product being built
        ↓
 Ruflo Agent Mesh  (ruflo/.agents/ + ruflo/.claude/)
```

**Agents:**

| Agent | Role |
|-------|------|
| `interface_agent` | React/Next.js UI, components, styling, API clients |
| `gotham_agent` | FastAPI, SQL, schema, architecture, security |
| `etl_agent` | Spring Batch, ETL pipelines, EPM integrations |
| `sql_agent` | Oracle SQL tuning, PL/SQL (ETL-focused) |
| `validation_agent` | Data quality, reconciliation |
| `memory_agent` | ChromaDB ingest and retrieval |

**How learning works:** Tasks are stored in ChromaDB after completion. Cloud sync adds docs from GitHub repos and URLs. RAG retrieves context on every request.

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r ai_agent/requirements.txt
```

### 2. Set environment variables

```bash
cp .env.example .env
# Add ANTHROPIC_API_KEY; optional GITHUB_TOKEN for cloud sync
```

### 3. Seed the knowledge base

```bash
python -m ai_agent.cli seed
```

### 4. Chat or run the API

```bash
python -m ai_agent.cli chat

uvicorn ai_agent.api.main:app --reload --port 8000
# Docs: http://localhost:8000/docs
```

### 5. Run the app scaffold (optional)

```bash
# Backend (port 8001)
cd app/backend && pip install -r requirements.txt && uvicorn main:app --reload --port 8001

# Frontend (port 3000)
cd app/frontend && npm install && npm run dev
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `python -m ai_agent.cli chat` | Interactive REPL |
| `python -m ai_agent.cli ask "build a user registration API and React form"` | One-shot task |
| `python -m ai_agent.cli ingest ./docs/app_patterns.md` | Ingest a file |
| `python -m ai_agent.cli kb-stats` | Knowledge base size |
| `python -m ai_agent.cli seed` | Seed ETL + React/FastAPI patterns |
| `python -m ai_agent.cli sync-github owner/repo` | Sync GitHub README + docs/ |
| `python -m ai_agent.cli sync-urls https://...` | Sync public URLs |

---

## REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/orchestrate` | Route task to specialist agents |
| `GET` | `/health` | Health + agent list |
| `POST` | `/reset-session` | Clear conversation history |
| `POST` | `/kb/ingest` | Add document to ChromaDB |
| `POST` | `/kb/query` | Query knowledge base |
| `GET` | `/kb/stats` | KB statistics |
| `POST` | `/kb/ingest-file` | Ingest local file (background) |
| `POST` | `/kb/sync/github` | Sync GitHub repo `{owner, repo, paths?}` |
| `POST` | `/kb/sync/urls` | Sync URLs `{urls: [...]}` |
| `POST` | `/kb/sync/all` | Run env-configured sync sources |
| `GET` | `/kb/sync/status` | Cloud sync status |

---

## Cloud Knowledge Sync

Phased approach:

1. **Manual** — `ingest`, `/kb/ingest`, memory agent
2. **GitHub** — `sync-github owner/repo` or `POST /kb/sync/github`
3. **URLs** — `sync-urls` or set `SYNC_URLS` in `.env`
4. **Scheduled** — cron or GitHub Actions calling CLI weekly

```bash
python -m ai_agent.cli sync-github facebook/react
curl -X POST http://localhost:8000/kb/sync/github \
  -H "Content-Type: application/json" \
  -d '{"owner": "tiangolo", "repo": "fastapi"}'
```

---

## Cursor IDE Subagents

Project subagents in `.cursor/agents/`:

| Subagent | Purpose |
|----------|---------|
| `interface` | Frontend React/Next.js work |
| `gotham` | Backend FastAPI, SQL, architecture |
| `env-dependencies` | Env and pip setup |
| `ci-pipeline` | AI agent CI workflow |
| `ai-agent-tester` | pytest and smoke tests |
| `ai-agent-docs` | This documentation |
| `etl-codebase` | Spring Boot ETL repo navigation |

```
Use the gotham subagent to design the orders API
Use the interface subagent to build the checkout page
```

---

## Ruflo Integration

Config in `ruflo/.agents/` and `ruflo/.claude/config.yaml`.

```bash
npm install -g claude-flow
npx claude-flow coordination swarm-init --config ruflo/.claude/config.yaml
```

---

## Project Structure

```
ai_agent/
├── orchestrator/orchestrator.py
├── rag/
│   ├── chroma_store.py
│   └── cloud_sync.py
├── agents/
│   ├── interface_agent.py
│   ├── gotham_agent.py
│   ├── etl_agent.py
│   ├── sql_agent.py
│   ├── data_validation_agent.py
│   └── memory_agent.py
├── api/main.py
├── tests/
├── cli.py
└── requirements.txt

app/                          # Product scaffold (Interface + Gotham)
├── frontend/                 # Next.js (port 3000)
├── backend/                  # FastAPI (port 8001)
└── README.md

ruflo/
├── .agents/                  # interface, gotham, sql, validation, memory YAML
└── .claude/config.yaml

.cursor/agents/               # Cursor IDE subagents
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | — | Anthropic API key |
| `CHROMA_PATH` | No | `./chroma_db` | ChromaDB path |
| `API_HOST` | No | `0.0.0.0` | Orchestration API host |
| `API_PORT` | No | `8000` | Orchestration API port |
| `GITHUB_TOKEN` | No | — | GitHub API for cloud sync |
| `CLOUD_SYNC_ENABLED` | No | `true` | Enable `/kb/sync/all` |
| `SYNC_URLS` | No | — | Comma-separated URLs to sync |
| `SYNC_GITHUB_REPO` | No | — | Default `owner/repo` for sync_all |
| `ORACLE_DB_URL` | No | — | Oracle (future live queries) |
