"""66degrees-factory CLI: init, list catalogs, serve."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from cli.catalog import get_domain, get_workflow, load_domains
from cli.choices import FactoryChoices, load_choices_file
from cli.copier import destination_exists_nonempty, generate_project
from cli.factory_catalog import assert_backend_allowed, load_factory_catalog
from cli.template_root import template_root
from config.project_config import load_project_config
from config.settings import PROJECT_ROOT

app = typer.Typer(help="66degrees multi-agent factory CLI", no_args_is_help=True)
console = Console()


def _print_summary(choices: FactoryChoices) -> None:
    table = Table(title="Project summary")
    table.add_column("Field")
    table.add_column("Value")
    rows = [
        ("Project", choices.project_name),
        ("Output", str(choices.dest())),
        ("Domain", choices.domain),
        ("Workflow", choices.workflow),
        ("Gateway", choices.gateway),
        ("Cache", choices.cache),
        ("Vector", choices.vector),
        ("Embeddings", choices.embeddings),
        ("Parser", choices.parser),
        ("Guardrails", choices.guardrails),
        ("Eval", choices.eval_backend),
        ("Langfuse", str(choices.langfuse)),
        ("Logfire", str(choices.logfire)),
        ("ADK", str(choices.adk)),
        ("A2A", str(choices.a2a)),
        ("Environment", choices.environment),
        ("Template", f"{choices.template_package} {choices.template_version}"),
    ]
    for key, value in rows:
        table.add_row(key, value)
    console.print(table)


@app.command("list-domains")
def list_domains() -> None:
    for domain in load_domains():
        console.print(domain.id)


@app.command("list-workflows")
def list_workflows(domain: Annotated[str, typer.Option("--domain")]) -> None:
    catalog = get_domain(domain)
    for workflow in catalog.workflows:
        console.print(f"{workflow.id:<20} {workflow.name}")


@app.command("list-factories")
def list_factories(
    capability: Annotated[str | None, typer.Option("--capability")] = None,
) -> None:
    catalog = load_factory_catalog()
    for cap in catalog.capabilities:
        if capability and cap.id != capability:
            continue
        console.print(f"[bold]{cap.id}[/bold]  {cap.prompt}")
        for backend in cap.backends:
            console.print(f"  {backend.id:<24} {backend.status}")


@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
) -> None:
    """Run the FastAPI app (replaces the old `factory` uvicorn launcher)."""
    import uvicorn

    from config.settings import get_settings

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=settings.debug,
    )


@app.command()
def init(
    name: Annotated[str | None, typer.Option("--name")] = None,
    output: Annotated[Path | None, typer.Option("--output")] = None,
    domain: Annotated[str | None, typer.Option("--domain")] = None,
    workflow: Annotated[str | None, typer.Option("--workflow")] = None,
    gateway: Annotated[str | None, typer.Option("--gateway")] = None,
    default_model: Annotated[str | None, typer.Option("--default-model")] = None,
    cache: Annotated[str | None, typer.Option("--cache")] = None,
    redis_url: Annotated[str | None, typer.Option("--redis-url")] = None,
    memcached_url: Annotated[str | None, typer.Option("--memcached-url")] = None,
    vector: Annotated[str | None, typer.Option("--vector")] = None,
    opensearch_url: Annotated[str | None, typer.Option("--opensearch-url")] = None,
    embeddings: Annotated[str | None, typer.Option("--embeddings")] = None,
    parser: Annotated[str | None, typer.Option("--parser")] = None,
    guardrails: Annotated[str | None, typer.Option("--guardrails")] = None,
    eval_backend: Annotated[str | None, typer.Option("--eval")] = None,
    langfuse: Annotated[
        bool | None,
        typer.Option("--langfuse/--no-langfuse"),
    ] = None,
    logfire: Annotated[bool | None, typer.Option("--logfire/--no-logfire")] = None,
    adk: Annotated[bool | None, typer.Option("--adk/--no-adk")] = None,
    a2a: Annotated[bool | None, typer.Option("--a2a/--no-a2a")] = None,
    mcp_examples: Annotated[
        bool | None,
        typer.Option("--mcp-examples/--no-mcp-examples"),
    ] = None,
    secrets_backend: Annotated[str | None, typer.Option("--secrets-backend")] = None,
    environment: Annotated[str | None, typer.Option("--environment")] = None,
    yes: Annotated[bool, typer.Option("--yes")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    force: Annotated[bool, typer.Option("--force")] = False,
    force_planned: Annotated[bool, typer.Option("--force-planned")] = False,
    from_choices: Annotated[Path | None, typer.Option("--from-choices")] = None,
) -> None:
    """Create a new project from this template (one domain + one workflow)."""
    if load_project_config(PROJECT_ROOT) is not None:
        console.print(
            "[yellow]Warning:[/yellow] this directory already has config/project.yaml. "
            "init creates a new project folder; it does not reconfigure the current one."
        )

    if from_choices is not None:
        choices = load_choices_file(from_choices)
        if name:
            choices.project_name = name
        if output:
            choices.output = output
        _finalize_init(choices, yes=True, dry_run=dry_run, force=force)
        return

    if yes and (not name or not domain or not workflow):
        raise typer.BadParameter("--yes requires --name, --domain, and --workflow")

    project_name = name or "my-agent-project"
    dest = output or Path(f"./{project_name}")
    slug = project_name.replace("-", "_").replace(" ", "_")

    partial = FactoryChoices(
        project_name=project_name,
        output=dest,
        slug=slug,
        domain=domain or "",
        workflow=workflow or "",
        gateway=gateway or "litellm",
        default_model=default_model or "gemini/gemini-2.5-flash",
        cache=cache or "memory",
        redis_url=redis_url or "redis://localhost:6379/0",
        memcached_url=memcached_url or "memcached://localhost:11211",
        vector=vector or "memory",
        opensearch_url=opensearch_url or "http://localhost:9200",
        embeddings=embeddings or "litellm",
        parser=parser or "docling",
        guardrails=guardrails or "passthrough",
        eval_backend=eval_backend or "local",
        langfuse=True if langfuse is None else langfuse,
        logfire=False if logfire is None else logfire,
        adk=False if adk is None else adk,
        a2a=False if a2a is None else a2a,
        mcp_examples=False if mcp_examples is None else mcp_examples,
        secrets_backend=secrets_backend or "env",
        environment=environment or "local",
    )

    if not yes:
        from cli.wizard import run_wizard

        choices = run_wizard(partial)
    else:
        get_domain(partial.domain)
        get_workflow(partial.domain, partial.workflow)
        try:
            assert_backend_allowed("gateway", partial.gateway, force_planned=force_planned)
            assert_backend_allowed("cache", partial.cache, force_planned=force_planned)
            assert_backend_allowed("vector", partial.vector, force_planned=force_planned)
            assert_backend_allowed("secrets", partial.secrets_backend, force_planned=force_planned)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        choices = partial

    _finalize_init(choices, yes=yes, dry_run=dry_run, force=force)


def _finalize_init(
    choices: FactoryChoices,
    *,
    yes: bool,
    dry_run: bool,
    force: bool,
) -> None:
    dest = choices.dest()
    if dest.resolve() == template_root().resolve():
        raise typer.BadParameter("Refusing to init into the template source directory")

    if destination_exists_nonempty(dest) and not force and not dry_run:
        raise typer.BadParameter(f"Destination is not empty: {dest} (use --force)")

    _print_summary(choices)
    if dry_run:
        planned = generate_project(choices, dry_run=True)
        console.print(f"[bold]Dry run[/bold] — would write {len(planned)} paths to {dest}")
        console.print(choices.render_env())
        return

    if not yes:
        if not typer.confirm("Create project?", default=True):
            raise typer.Abort()

    if force and dest.exists():
        import shutil

        shutil.rmtree(dest)

    generate_project(choices, dry_run=False)
    console.print(f"Copied template → {dest}")
    console.print(f"Wrote domains/{choices.domain}/workflows/{choices.workflow}/")
    console.print("Wrote .env, config/project.yaml, factory-choices.json")
    console.print("\nNext:")
    console.print(f"  cd {dest}")
    for hint in choices.extras_hints():
        console.print(f"  {hint}")
    console.print("  # set GOOGLE_API_KEY (and other CHANGE_ME keys)")
    console.print("  make dev")
