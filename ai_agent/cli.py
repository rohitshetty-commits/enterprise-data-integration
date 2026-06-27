#!/usr/bin/env python3
"""
CLI for the Enterprise ETL AI Orchestrator.

Usage:
  python -m ai_agent.cli                          # interactive REPL
  python -m ai_agent.cli ask "design a batch job" # one-shot
  python -m ai_agent.cli ingest ./docs/etl.md     # ingest a file
  python -m ai_agent.cli kb-stats                 # show knowledge base size
  python -m ai_agent.cli seed                     # seed initial knowledge
  python -m ai_agent.cli sync-github owner/repo   # sync GitHub repo to KB
  python -m ai_agent.cli sync-urls https://...    # sync URLs to KB
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from dotenv import load_dotenv
import os

load_dotenv()

app = typer.Typer(help="Enterprise ETL AI Orchestrator CLI")
console = Console()


def get_orchestrator():
    from ai_agent.orchestrator.orchestrator import OrchestratorAgent
    return OrchestratorAgent()


@app.command()
def ask(task: str = typer.Argument(..., help="Task to send to the orchestrator")):
    """Send a single task to the orchestrator and print the result."""
    console.print(Panel(f"[bold cyan]Task:[/bold cyan] {task}", expand=False))
    orch = get_orchestrator()
    result = orch.run(task, verbose=True)
    console.print(Panel(Markdown(result), title="[green]Result[/green]", expand=True))


@app.command()
def chat():
    """Start an interactive REPL session with the orchestrator."""
    console.print(Panel(
        "[bold green]App Builder AI Orchestrator[/bold green]\n"
        "Agents: Interface (frontend), Gotham (backend), ETL, SQL, Validation, Memory\n"
        "Type your task and press Enter. Type [red]exit[/red] to quit.",
        title="Multi-Agent System"
    ))
    orch = get_orchestrator()
    while True:
        try:
            user_input = console.input("\n[bold cyan]You:[/bold cyan] ").strip()
            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[yellow]Goodbye![/yellow]")
                break
            if not user_input:
                continue
            result = orch.run(user_input, verbose=True)
            console.print(Panel(Markdown(result), title="[green]Orchestrator[/green]"))
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Goodbye![/yellow]")
            break


@app.command()
def ingest(filepath: str = typer.Argument(..., help="Path to file to ingest into knowledge base")):
    """Ingest a text/markdown file into the ChromaDB knowledge base."""
    from ai_agent.rag.chroma_store import ChromaStore
    if not os.path.exists(filepath):
        console.print(f"[red]File not found: {filepath}[/red]")
        raise typer.Exit(1)
    store = ChromaStore()
    count = store.ingest_file(filepath)
    console.print(f"[green]Ingested {count} chunks from '{filepath}'[/green]")
    console.print(f"[blue]Knowledge base now has {store.count()} total documents[/blue]")


@app.command(name="kb-stats")
def kb_stats():
    """Show knowledge base statistics."""
    from ai_agent.rag.chroma_store import ChromaStore
    store = ChromaStore()
    console.print(Panel(
        f"[bold]Total Documents:[/bold] {store.count()}\n"
        f"[bold]Collection:[/bold] enterprise_etl_knowledge\n"
        f"[bold]Path:[/bold] {os.getenv('CHROMA_PATH', './chroma_db')}",
        title="Knowledge Base Stats"
    ))


def _seed_docs():
    return [
        {
            "text": "Spring Batch Job structure: A Job contains Steps. Each Step has ItemReader, ItemProcessor, ItemWriter. Use chunk-oriented processing for large datasets. Configure commit-interval for performance tuning.",
            "metadata": {"source": "seed", "type": "pattern", "topic": "spring_batch"},
        },
        {
            "text": "Oracle ETL pattern for delta loads: Use a HIGH_WATERMARK table to track last extracted timestamp. SELECT * FROM source_table WHERE last_modified > :last_hwm. Update HWM after successful load.",
            "metadata": {"source": "seed", "type": "pattern", "topic": "oracle_etl"},
        },
        {
            "text": "FDMEE integration pattern: Data is loaded via EPM Automate CLI. Use loadData command with a batch file. Validate with validateData before export to HFM. Always check error logs in %EPM_LOG_HOME%.",
            "metadata": {"source": "seed", "type": "pattern", "topic": "fdmee"},
        },
        {
            "text": "SCD Type 2 pattern in Oracle: Use MERGE statement. When source row differs from target on tracked columns, set IS_CURRENT='N' and END_DATE=SYSDATE on old record, insert new record with IS_CURRENT='Y' and START_DATE=SYSDATE.",
            "metadata": {"source": "seed", "type": "pattern", "topic": "scd"},
        },
        {
            "text": "Maven Spring Boot project structure for ETL: src/main/java contains batch config, jobs, steps, readers, processors, writers. src/main/resources has application.properties with datasource and batch configs. Use @EnableBatchProcessing on main class.",
            "metadata": {"source": "seed", "type": "pattern", "topic": "project_structure"},
        },
        {
            "text": "Data validation best practice: Always validate row counts (source vs target), sum of key financial columns, null checks on mandatory fields, and referential integrity before marking a batch run as SUCCESS.",
            "metadata": {"source": "seed", "type": "pattern", "topic": "validation"},
        },
        {
            "text": "Ruflo agent orchestration: Use swarm topology for parallel ETL tasks. Assign etl_agent for pipeline design, sql_agent for query optimization, validation_agent for data quality, memory_agent for knowledge persistence.",
            "metadata": {"source": "seed", "type": "pattern", "topic": "ruflo"},
        },
        {
            "text": "FastAPI backend pattern: Organize app/backend with routes/, models/, services/, db/. Use Pydantic for request/response. Version APIs under /api/v1/. Enable CORS for localhost:3000. Error format: {\"detail\": \"message\", \"code\": \"ERROR_CODE\"}.",
            "metadata": {"source": "seed", "type": "pattern", "topic": "fastapi"},
        },
        {
            "text": "React Next.js frontend pattern: Use TypeScript, App Router in src/app/, components in src/components/, API client in src/lib/api.ts with NEXT_PUBLIC_API_URL. Always handle loading, error, and empty states.",
            "metadata": {"source": "seed", "type": "pattern", "topic": "react"},
        },
        {
            "text": "Full-stack agent workflow: Gotham agent designs FastAPI routes and schema first. Interface agent builds React UI calling those endpoints. Orchestrator uses follow_up_agent for sequential Gotham then Interface routing.",
            "metadata": {"source": "seed", "type": "pattern", "topic": "agent_workflow"},
        },
        {
            "text": "Monorepo app layout: app/frontend (Next.js port 3000), app/backend (FastAPI port 8001). ai_agent API on port 8000 is orchestration only, not the product API.",
            "metadata": {"source": "seed", "type": "pattern", "topic": "monorepo"},
        },
    ]


@app.command()
def seed():
    """Seed the knowledge base with ETL and React/FastAPI app-building patterns."""
    from ai_agent.rag.chroma_store import ChromaStore
    store = ChromaStore()

    seed_docs = _seed_docs()
    texts = [d["text"] for d in seed_docs]
    metas = [d["metadata"] for d in seed_docs]
    store.add_documents(texts, metas)

    patterns_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "docs",
        "app_patterns.md",
    )
    if os.path.exists(patterns_path):
        chunks = store.ingest_file(patterns_path)
        console.print(f"[blue]Also ingested docs/app_patterns.md ({chunks} chunks)[/blue]")

    console.print(f"[green]Seeded {len(seed_docs)} base knowledge documents[/green]")
    console.print(f"[blue]Knowledge base now has {store.count()} total documents[/blue]")


@app.command(name="sync-github")
def sync_github(
    repo_slug: str = typer.Argument(..., help="GitHub repo as owner/repo"),
):
    """Sync README and docs/ from a GitHub repository into the knowledge base."""
    if "/" not in repo_slug:
        console.print("[red]Use format: owner/repo[/red]")
        raise typer.Exit(1)
    owner, repo = repo_slug.split("/", 1)
    from ai_agent.rag.cloud_sync import CloudSyncService
    sync = CloudSyncService()
    result = sync.sync_github_repo(owner.strip(), repo.strip())
    console.print(Panel(
        f"[bold]Added:[/bold] {result['added']}\n"
        f"[bold]Skipped:[/bold] {result['skipped']}\n"
        f"[bold]Errors:[/bold] {len(result['errors'])}\n"
        f"[bold]KB total:[/bold] {sync.chroma.count()}",
        title=f"GitHub sync: {repo_slug}"
    ))
    if result["errors"]:
        for err in result["errors"][:5]:
            console.print(f"[yellow]{err}[/yellow]")


@app.command(name="sync-urls")
def sync_urls_cmd(
    urls: list[str] = typer.Argument(..., help="URLs to fetch and ingest"),
):
    """Fetch public URLs and ingest into the knowledge base."""
    from ai_agent.rag.cloud_sync import CloudSyncService
    sync = CloudSyncService()
    result = sync.sync_urls(urls)
    console.print(Panel(
        f"[bold]Added:[/bold] {result['added']}\n"
        f"[bold]Skipped:[/bold] {result['skipped']}\n"
        f"[bold]KB total:[/bold] {sync.chroma.count()}",
        title="URL sync"
    ))


if __name__ == "__main__":
    app()
