"""Staged interactive init: dest, domain, workflow, plan, stack."""

from __future__ import annotations

from pathlib import Path

from cli.catalog import (
    CatalogAgent,
    CatalogGraph,
    CatalogGraphNode,
    CatalogWorkflow,
    clone_workflow,
    get_domain,
    get_workflow,
    load_domains,
    resolve_domain_id,
    resolve_workflow_id,
    validate_slug,
)
from cli.choices import FactoryChoices
from cli.copier import destination_exists_nonempty
from cli.dest import dest_mode_label, slugify, suggest_dest
from cli.factory_catalog import backend_id_from_label, get_capability, labeled_backend_choices
from cli.template_root import template_root
from cli.ui import print_header, print_hint, print_plan_card, questionary_style, stack_one_liner

BACK = "<< Back"


def _style():
    return questionary_style()


def _select(message: str, choices: list[str], default: str | None = None) -> str:
    import questionary

    kwargs: dict = {"choices": choices, "style": _style()}
    if default is not None and default in choices:
        kwargs["default"] = default
    result = questionary.select(message, **kwargs).ask()
    if result is None:
        raise SystemExit("Cancelled")
    return result


def _text(message: str, default: str) -> str:
    import questionary

    result = questionary.text(message, default=default, style=_style()).ask()
    if result is None:
        raise SystemExit("Cancelled")
    return result


def _confirm(message: str, default: bool) -> bool:
    import questionary

    result = questionary.confirm(message, default=default, style=_style()).ask()
    if result is None:
        raise SystemExit("Cancelled")
    return result


def _select_backend(capability: str, current: str, *, include_planned: bool) -> str:
    cap = get_capability(capability)
    labels = labeled_backend_choices(
        capability, include_planned=include_planned, current=current
    )
    if not labels:
        raise SystemExit(f"No implemented backends for {capability}")
    default = next((label for label in labels if backend_id_from_label(label) == current), labels[0])
    picked = _select(cap.prompt, labels, default)
    return backend_id_from_label(picked)


def _customize_plan(workflow: CatalogWorkflow) -> CatalogWorkflow:
    agents: list[CatalogAgent] = []
    nodes: list[CatalogGraphNode] = []
    for node in workflow.graph.nodes:
        agent = next((a for a in workflow.agents if a.name == node.agent_name), None)
        if agent is None:
            continue
        action = _select(
            f"Agent {agent.name}",
            ["Keep", "Drop", "Edit HITL / tools"],
            "Keep",
        )
        if action == "Drop":
            continue
        hitl = node.requires_hitl
        tools = list(agent.allowed_tools)
        if action == "Edit HITL / tools":
            hitl = _confirm("Requires human approval (HITL)?", hitl)
            tools_raw = _text("Tools (comma-separated)", ", ".join(tools))
            tools = [t.strip() for t in tools_raw.split(",") if t.strip()]
        agents.append(agent.model_copy(update={"allowed_tools": tools}))
        nodes.append(node.model_copy(update={"requires_hitl": hitl, "next": []}))

    if _confirm("Add one extra agent?", False):
        name = _text("New agent name", "custom_agent")
        desc = _text("Description", "Custom step")
        prompt = _text("Prompt", "You are a helpful agent. Stay within the query facts.")
        extra = CatalogAgent(name=name, description=desc, prompt_stub=prompt)
        agents.append(extra)
        nodes.append(CatalogGraphNode(id=name, agent_name=name, next=[]))

    if not agents:
        raise SystemExit("Plan must keep at least one agent")

    for i, node in enumerate(nodes):
        node.next = [nodes[i + 1].id] if i + 1 < len(nodes) else []

    return workflow.model_copy(
        update={
            "agents": agents,
            "graph": CatalogGraph(entry=nodes[0].id, nodes=nodes),
        }
    )


def _configure_backends(partial: FactoryChoices, *, full: bool, include_planned: bool) -> FactoryChoices:
    from cli.ui import console

    gateway = _select_backend("gateway", partial.gateway, include_planned=include_planned)
    default_model = partial.default_model
    bedrock_region = partial.bedrock_region
    bedrock_model_id = partial.bedrock_model_id
    ollama_url = partial.ollama_url
    ollama_model = partial.ollama_model
    if gateway == "bedrock":
        bedrock_region = _text("Bedrock region", bedrock_region)
        bedrock_model_id = _text("Bedrock model id", bedrock_model_id)
    elif gateway == "ollama":
        ollama_url = _text("Ollama base URL", ollama_url)
        ollama_model = _text("Ollama model", ollama_model)
    else:
        default_model = _text("Default model", default_model)

    cache = _select_backend("cache", partial.cache, include_planned=include_planned)
    redis_url = partial.redis_url
    memcached_url = partial.memcached_url
    if cache == "redis":
        redis_url = _text("Redis URL", redis_url)
    if cache == "memcached":
        memcached_url = _text("Memcached URL", memcached_url)

    vector = _select_backend("vector", partial.vector, include_planned=include_planned)
    opensearch_url = partial.opensearch_url
    qdrant_url = partial.qdrant_url
    embeddings = partial.embeddings
    if vector != "memory":
        opensearch_url = (
            _text("OpenSearch URL", opensearch_url) if vector == "opensearch" else opensearch_url
        )
        qdrant_url = _text("Qdrant URL", qdrant_url) if vector == "qdrant" else qdrant_url
        embeddings = _select_backend("embeddings", embeddings, include_planned=include_planned)

    console.print(f"  [dim]{stack_one_liner(gateway=gateway, cache=cache, vector=vector)}[/dim]")

    parser = partial.parser
    parser_labels = labeled_backend_choices("parser", include_planned=include_planned)
    if full and len(parser_labels) > 1:
        parser = _select_backend("parser", parser, include_planned=include_planned)

    guardrails = _select_backend("guardrails", partial.guardrails, include_planned=include_planned)
    eval_backend = _select_backend("eval", partial.eval_backend, include_planned=include_planned)
    langfuse = _confirm("Enable Langfuse", False)
    logfire = _confirm("Enable Logfire", partial.logfire)
    looker = _confirm("Enable Looker", partial.looker)
    looker_base_url = partial.looker_base_url
    if looker:
        looker_base_url = _text("Looker base URL", looker_base_url or "https://your.cloud.looker.com")
    bqml = _confirm("Enable BigQuery ML", partial.bqml)
    bqml_project = partial.bqml_project
    bqml_location = partial.bqml_location
    bqml_dataset = partial.bqml_dataset
    bqml_model = partial.bqml_model
    if bqml:
        bqml_project = _text("BigQuery project", bqml_project)
        bqml_location = _text("BigQuery location", bqml_location)
        bqml_dataset = _text("BQML dataset", bqml_dataset)
        bqml_model = _text("Default BQML model id", bqml_model)
    state_backend = _select_backend("state", partial.state_backend, include_planned=include_planned)
    adk = partial.adk
    a2a = partial.a2a
    mcp_examples = partial.mcp_examples
    secrets_backend = partial.secrets_backend
    tenant_isolation = partial.tenant_isolation
    environment = partial.environment
    if full:
        adk = _confirm("Enable Google ADK", adk)
        a2a = _confirm("Enable A2A", a2a)
        mcp_examples = _confirm("Include MCP connection examples", mcp_examples)
        secrets_backend = _select_backend(
            "secrets", secrets_backend, include_planned=include_planned
        )
        tenant_isolation = _select(
            "Tenant isolation (logical = shared DB keys)",
            ["logical", "namespace", "dedicated"],
            tenant_isolation,
        )
        environment = _select(
            "Environment overlay",
            ["local", "dev", "test"],
            environment if environment in {"local", "dev", "test"} else "local",
        )

    return partial.model_copy(
        update={
            "gateway": gateway,
            "default_model": default_model,
            "bedrock_region": bedrock_region,
            "bedrock_model_id": bedrock_model_id,
            "ollama_url": ollama_url,
            "ollama_model": ollama_model,
            "cache": cache,
            "redis_url": redis_url,
            "memcached_url": memcached_url,
            "vector": vector,
            "opensearch_url": opensearch_url,
            "qdrant_url": qdrant_url,
            "embeddings": embeddings,
            "parser": parser,
            "guardrails": guardrails,
            "eval_backend": eval_backend,
            "langfuse": langfuse,
            "logfire": logfire,
            "looker": looker,
            "looker_base_url": looker_base_url,
            "bqml": bqml,
            "bqml_project": bqml_project,
            "bqml_location": bqml_location,
            "bqml_dataset": bqml_dataset,
            "bqml_model": bqml_model,
            "state_backend": state_backend,
            "adk": adk,
            "a2a": a2a,
            "mcp_examples": mcp_examples,
            "secrets_backend": secrets_backend,
            "tenant_isolation": tenant_isolation,
            "environment": environment,
        }
    )


def _stage_location(partial: FactoryChoices) -> tuple[str, Path]:
    from cli.ui import console

    print_header(1, 4, "Location")
    suggestion = suggest_dest(
        name=None if partial.project_name == "my-agent-project" else partial.project_name,
        output=None if str(partial.output) in {".", str(Path(f"./{partial.project_name}"))} else partial.output,
    )
    console.print(f"  You are in   {suggestion.cwd}")
    if suggestion.is_template:
        console.print("  [yellow]This is the factory repo. Init cannot write here.[/yellow]")
    elif suggestion.cwd_empty:
        console.print("  This folder is empty.")
    else:
        console.print("  This folder is not empty.")
    print_hint()

    name = suggestion.project_name
    output = suggestion.output

    if suggestion.mode == "this_folder":
        if _confirm(f'Create project "{name}" in this folder?', True):
            return name, output
        name = _text("Project name", name)
        output = Path(_text("Output directory", str(Path.home() / "Desktop" / name))).expanduser()
    elif suggestion.mode == "factory_repo":
        name = _text("Project name", name)
        output = Path(_text("Output directory", str(Path.home() / "Desktop" / name))).expanduser()
    else:
        name = _text("Project name", name)
        if _confirm(f'Create a subfolder "{name}" here?', True):
            output = suggestion.cwd / name
        else:
            output = Path(_text("Output directory", str(output))).expanduser()

    while True:
        dest = output.expanduser().resolve()
        if dest == template_root().resolve():
            console.print("[red]Refusing the template source directory.[/red]")
            output = Path(_text("Output directory", str(Path.home() / "Desktop" / name))).expanduser()
            continue
        if destination_exists_nonempty(dest):
            console.print(f"[red]Destination is not empty:[/red] {dest}")
            output = Path(_text("Output directory", str(output))).expanduser()
            continue
        return name, output


def run_wizard(partial: FactoryChoices, *, force_planned: bool = False) -> FactoryChoices:
    from cli.ui import console

    name, output = _stage_location(partial)
    slug = slugify(name)

    domains = [d for d in load_domains() if d.id != "other"] + [
        d for d in load_domains() if d.id == "other"
    ]
    domain: str | None = partial.domain or None
    workflow_id: str | None = partial.workflow or None
    plan_workflow: CatalogWorkflow | None = None
    plan_mode = "accepted"
    custom = False

    stage = "domain" if not domain else ("workflow" if not workflow_id else "plan")
    while True:
        if stage == "domain":
            print_header(2, 4, "Domain")
            print_hint()
            labels = {f"{d.id} — {d.name}": d.id for d in domains}
            picked = _select("Domain", [*labels, BACK] if domain else list(labels))
            if picked == BACK:
                continue
            domain = resolve_domain_id(labels[picked])
            workflow_id = None
            plan_workflow = None
            custom = domain == "other"
            stage = "name_custom" if custom else "workflow"
            continue
        if stage == "name_custom":
            print_header(3, 4, "Name")
            print_hint()
            try:
                domain = validate_slug(_text("Domain id (slug)", "acme"), kind="domain")
                _text("Domain display name", domain)
                workflow_id = validate_slug(_text("Workflow id (slug)", "intake"), kind="workflow")
                wf_name = _text("Workflow display name", workflow_id)
            except ValueError as exc:
                from cli.ui import console

                console.print(f"[red]{exc}[/red]")
                continue
            plan_workflow = clone_workflow(
                get_workflow("other", "custom"),
                id=workflow_id,
                name=wf_name,
            )
            custom = True
            stage = "plan"
            continue
        if stage == "workflow":
            print_header(3, 4, "Workflow")
            print_hint()
            catalog = get_domain(domain or domains[0].id)
            labels = {f"{w.id} — {w.name}": w.id for w in catalog.workflows}
            picked = _select("Workflow", [*labels, BACK])
            if picked == BACK:
                stage = "domain"
                continue
            workflow_id = resolve_workflow_id(catalog.id, labels[picked])
            domain = catalog.id
            plan_workflow = None
            stage = "plan"
            continue
        print_header(4, 4, "Plan")
        if plan_workflow is None:
            plan_workflow = get_workflow(domain or "", workflow_id or "")
        print_plan_card(plan_workflow)
        print_hint()
        decision = _select(
            "Use this plan?",
            ["Accept this plan", "Change stack", "Customize agents", BACK],
            "Accept this plan",
        )
        if decision == BACK:
            stage = "name_custom" if custom else "workflow"
            continue
        if decision == "Customize agents":
            plan_workflow = _customize_plan(plan_workflow)
            plan_mode = "customized"
        else:
            plan_mode = "accepted"
        change_stack = decision == "Change stack" or plan_mode == "customized"
        break

    assert domain and workflow_id and plan_workflow
    stack = plan_workflow.recommended_stack
    dest = output.expanduser().resolve()
    choices = partial.model_copy(
        update={
            "project_name": name,
            "output": output,
            "slug": slug,
            "domain": domain,
            "workflow": workflow_id,
            "gateway": stack.gateway,
            "cache": stack.cache,
            "vector": stack.vector,
            "langfuse": False,
            "plan_mode": plan_mode,
            "dest_mode": dest_mode_label(dest),
            "workflow_plan": plan_workflow.model_dump(),
        }
    )

    if change_stack:
        choices = _configure_backends(
            choices, full=plan_mode == "customized", include_planned=force_planned
        )
    else:
        console.print(f"  [dim]Keeping {stack_one_liner(gateway=stack.gateway, cache=stack.cache, vector=stack.vector)}[/dim]")

    choices.plan_mode = plan_mode
    choices.workflow_plan = plan_workflow.model_dump()
    return choices
