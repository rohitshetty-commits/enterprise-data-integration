# App — Full-Stack Scaffold

React/Next.js frontend + Python FastAPI backend. Built and extended by **Interface** and **Gotham** agents.

## Layout

```
app/
├── frontend/          # Next.js (port 3000)
│   └── src/
│       ├── app/       # App Router pages
│       ├── components/
│       ├── hooks/
│       └── lib/       # API client
├── backend/           # FastAPI product API (port 8001)
│   ├── main.py
│   ├── routes/
│   ├── models/
│   ├── services/
│   └── db/
└── README.md
```

## Ports

| Service | Port | Purpose |
|---------|------|---------|
| `ai_agent` API | 8000 | Orchestrator / knowledge base (do not confuse with product API) |
| `app/backend` | 8001 | Product FastAPI application |
| `app/frontend` | 3000 | Next.js dev server |

## Quick start

### Backend

```bash
cd app/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Frontend

```bash
cd app/frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8001` in `app/frontend/.env.local`.

## Agent conventions

- **Gotham** adds routes in `app/backend/routes/`, models in `app/backend/models/`
- **Interface** adds pages in `app/frontend/src/app/`, components in `app/frontend/src/components/`
- Always document API contracts when adding endpoints so Interface can wire the UI
