# React + FastAPI App Patterns

## Monorepo layout

```
app/
├── frontend/     # Next.js on port 3000
└── backend/      # FastAPI on port 8001
```

The ai_agent orchestration API runs on port 8000 and is separate from the product API.

## FastAPI backend patterns

- Use Pydantic models for request and response bodies on every endpoint.
- Organize code: routes/ (HTTP), services/ (business logic), models/ (schemas), db/ (persistence).
- Enable CORS for http://localhost:3000 during development.
- Standard error format: {"detail": "human message", "code": "ERROR_CODE"}.
- Health check at GET /health for load balancers and Docker.
- Version APIs under /api/v1/ prefix.

## React / Next.js frontend patterns

- Use TypeScript for all components and API clients.
- Place reusable UI in src/components/, pages in src/app/ (App Router).
- API client in src/lib/api.ts with NEXT_PUBLIC_API_URL env var.
- Every data-fetching view must handle loading, error, and empty states.
- Define TypeScript interfaces matching Gotham Pydantic response models.

## Full-stack workflow

1. Gotham designs API + schema first (app/backend/).
2. Interface builds UI calling those endpoints (app/frontend/).
3. Orchestrator can route with follow_up: gotham_agent then interface_agent.

## REST conventions

- GET for reads, POST for creates, PUT/PATCH for updates, DELETE for removals.
- Return 201 with created resource on POST success.
- Return 404 with detail when resource not found.
- Use pagination: ?page=1&limit=20 with response { items, total, page, limit }.
