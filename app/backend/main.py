"""
Product FastAPI application — separate from ai_agent orchestration API (port 8000).
Run: uvicorn main:app --reload --port 8001
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="App API",
    description="Product backend built by Gotham agent",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy", "service": "app-backend"}


@app.get("/api/v1/hello", tags=["Demo"])
async def hello():
    return {"message": "Hello from Gotham backend"}
