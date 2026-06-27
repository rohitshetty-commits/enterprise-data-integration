# 🤖 AI Agent Layer — Enterprise Data Integration

A Python multi-agent orchestration layer built on top of the existing Spring Boot ETL framework.  
Uses **Claude (claude-sonnet-4-6)** + **ChromaDB RAG** + **Ruflo** to give the ETL system a conversational, self-learning AI brain.

---

## Architecture

```
User / API Request
        ↓
 OrchestratorAgent  ←──── ChromaDB (RAG knowledge base)
   ↙    ↓    ↘    ↘
ETL   SQL   Validation  Memory
Agent Agent   Agent     Agent
        ↓
 FastAPI REST API  (port 8000)
        ↓
 Ruflo Agent Mesh  (.agents/ + .claude/)
```

**How learning works:**  
Every task the orchestrator handles is stored back into ChromaDB.  
Next time a similar question is asked, the relevant context is retrieved automatically (RAG), making every answer better over time.

---

## Quick Start

### 1. Install dependencies

```bash
cd ai_agent
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Seed the knowledge base

```bash
python -m ai_agent.cli seed
```

### 4. Start interactive chat

```bash
python -m ai_agent.cli chat
```

### 5. Or start the REST API

```bash
uvicorn ai_agent.api.main:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `python -m ai_agent.cli chat` | Interactive REPL with the orchestrator |
| `python -m ai_agent.cli ask "design a delta load job"` | One-shot task |
| `python -m ai_agent.cli ingest ./docs/etl_patterns.md` | Ingest a file into knowledge base |
| `python -m ai_agent.cli kb-stats` | Show knowledge base document count |
| `python -m ai_agent.cli seed` | Seed base ETL knowledge patterns |

---

## REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/orchestrate` | Send any task to the orchestrator |
| `GET`  | `/health` | Health check + agent list |
| `POST` | `/kb/ingest` | Add a document to ChromaDB |
| `POST` | `/kb/query` | Query the knowledge base |
| `GET`  | `/kb/stats` | Knowledge base statistics |
| `POST` | `/reset-session` | Clear conversation history |

Full interactive docs: **http://localhost:8000/docs**

---

## Ruflo Integration

The `.agents/` and `.claude/` directories configure this project for the [Ruflo](https://github.com/ruvnet/ruflo) agent mesh.

```bash
# Install Ruflo CLI
npm install -g claude-flow

# Initialize swarm from this project's config
npx claude-flow coordination swarm-init --config ruflo/.claude/config.yaml

# Run a task across the swarm
npx claude-flow coordination task-orchestrate \
  --task "Design a Spring Batch job to load GL data from Oracle to HFM" \
  --strategy parallel
```

---

## Adding New Knowledge

Any of these methods adds new knowledge that all agents immediately benefit from:

```bash
# Ingest a markdown/text file
python -m ai_agent.cli ingest ./docs/new_etl_pattern.md

# Via REST API
curl -X POST http://localhost:8000/kb/ingest \
  -H "Content-Type: application/json" \
  -d '{"text": "Your new knowledge here", "metadata": {"source": "manual", "topic": "etl"}}'

# Memory agent via orchestrator
python -m ai_agent.cli ask "store: SCD Type 3 pattern uses current and prior value columns"
```

---

## Project Structure

```
ai_agent/
├── orchestrator/
│   └── orchestrator.py        # Main orchestrator — routes tasks, manages RAG
├── rag/
│   └── chroma_store.py        # ChromaDB wrapper — store, query, ingest files
├── agents/
│   ├── etl_agent.py           # Spring Batch / ETL pipeline specialist
│   ├── sql_agent.py           # Oracle SQL specialist
│   ├── data_validation_agent.py  # Data quality specialist
│   └── memory_agent.py        # Knowledge base manager
├── api/
│   └── main.py                # FastAPI REST server
├── tests/
│   └── test_smoke.py          # Smoke tests
├── cli.py                     # Typer CLI entry point
└── requirements.txt

ruflo/
├── .agents/
│   ├── etl_orchestrator.yaml  # Primary orchestrator agent definition
│   └── sub_agents.yaml        # SQL, validation, memory sub-agents
└── .claude/
    └── config.yaml            # Ruflo harness configuration
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | — | Your Anthropic API key |
| `CHROMA_PATH` | No | `./chroma_db` | Where ChromaDB persists data |
| `API_HOST` | No | `0.0.0.0` | FastAPI bind host |
| `API_PORT` | No | `8000` | FastAPI port |
| `ORACLE_DB_URL` | No | — | Oracle connection for live queries |
