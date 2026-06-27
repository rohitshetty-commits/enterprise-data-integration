#!/usr/bin/env python3
"""
CLI for the Enterprise ETL AI Orchestrator.

Usage:
  python -m ai_agent.cli                          # interactive REPL
  python -m ai_agent.cli ask "design a batch job" # one-shot
  python -m ai_agent.cli ingest ./docs/etl.md     # ingest a file
  python -m ai_agent.cli kb-stats                 # show knowledge base size
  python -m ai_agent.cli seed                     # seed initial ETL knowledge
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
        "[bold green]Enterprise ETL AI Orchestrator[/bold green]\n"
        "Type your task and press Enter. Type [red]exit[/red] to quit.",
        title="🤖 Multi-Agent System"
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
    console.print(f"[green]✅ Ingested {count} chunks from '{filepath}'[/green]")
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
        title="📚 Knowledge Base Stats"
    ))


@app.command()
def seed():
    """Seed the knowledge base with base ETL patterns and project context."""
    from ai_agent.rag.chroma_store import ChromaStore
    store = ChromaStore()

    seed_docs = [
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
    ]

    texts = [d["text"] for d in seed_docs]
    metas = [d["metadata"] for d in seed_docs]
    store.add_documents(texts, metas)
    console.print(f"[green]✅ Seeded {len(seed_docs)} base knowledge documents[/green]")
    console.print(f"[blue]Knowledge base now has {store.count()} total documents[/blue]")


if __name__ == "__main__":
    app()
