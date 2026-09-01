"""Rich + Questionary chrome for init (no extra TUI framework)."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cli.catalog import CatalogWorkflow, graph_chain
from cli.factory_catalog import get_capability

console = Console()

STACK_NEEDS = {
    "redis": "Needs Redis (CACHE_REDIS_URL)",
    "memcached": "Needs Memcached (CACHE_MEMCACHED_URL)",
    "opensearch": "Needs OpenSearch (VECTOR_OPENSEARCH_URL)",
    "qdrant": "Needs Qdrant (VECTOR_QDRANT_URL)",
    "ollama": "Needs a local Ollama (OLLAMA_BASE_URL)",
    "openai": "Needs OPENAI_API_KEY in .env",
    "bedrock": "Needs AWS credentials for Bedrock",
}


def questionary_style():
    from questionary import Style

    return Style(
        [
            ("qmark", "fg:cyan bold"),
            ("question", "bold"),
            ("answer", "fg:cyan"),
            ("pointer", "fg:cyan bold"),
            ("highlighted", "fg:cyan"),
            ("selected", "fg:cyan"),
            ("instruction", "fg:grey"),
        ]
    )


def print_header(stage: int, total: int, title: str) -> None:
    console.print()
    console.print("[bold]66degrees-factory[/bold]  [dim]·  new project[/dim]")
    console.print(f"[cyan]{stage}/{total}[/cyan]  {title}")
    console.print()


def print_hint() -> None:
    console.print("[dim]↑↓ enter  ·  esc cancel  ·  Back to go back[/dim]")


def stack_one_liner(*, gateway: str, cache: str, vector: str) -> str:
    return f"LLM {gateway}  ·  cache {cache}  ·  vector {vector}"


def stack_needs(*backends: str) -> list[str]:
    seen: list[str] = []
    for backend in backends:
        line = STACK_NEEDS.get(backend)
        if line and line not in seen:
            seen.append(line)
    return seen


def capability_label(capability_id: str) -> str:
    return get_capability(capability_id).prompt


def print_plan_card(workflow: CatalogWorkflow) -> None:
    stack = workflow.recommended_stack
    console.print(Panel(workflow.summary, title=workflow.name, border_style="cyan"))
    console.print(f"  [dim]Graph[/dim]  {graph_chain(workflow)}")
    console.print()

    platform = Table(title="Platform stack", show_header=True, header_style="bold")
    platform.add_column("Layer")
    platform.add_column("Choice")
    platform.add_row(capability_label("gateway"), stack.gateway)
    platform.add_row(capability_label("cache"), stack.cache)
    platform.add_row(capability_label("vector"), stack.vector)
    console.print(platform)
    needs = stack_needs(stack.gateway, stack.cache, stack.vector)
    if needs:
        for line in needs:
            console.print(f"  [dim]{line}[/dim]")
    console.print(f"  [dim]{stack_one_liner(gateway=stack.gateway, cache=stack.cache, vector=stack.vector)}[/dim]")
    console.print()

    agents = Table(title="Agents", show_header=True, header_style="bold")
    agents.add_column("Agent")
    agents.add_column("Role")
    agents.add_column("Agent tools")
    for agent in workflow.agents:
        agents.add_row(agent.name, agent.description, ", ".join(agent.allowed_tools) or "—")
    console.print(agents)
