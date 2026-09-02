"""Catalog schema tests."""

from cli.catalog import get_domain, get_workflow, load_domains, resolve_domain_id


def test_all_domain_catalogs_validate():
    domains = load_domains()
    ids = {d.id for d in domains}
    assert ids == {"bfs", "hcls", "retail"}
    for domain in domains:
        assert domain.workflows
        seen = set()
        for workflow in domain.workflows:
            assert workflow.id not in seen
            seen.add(workflow.id)
            assert workflow.agents
            assert workflow.summary
            node_ids = {n.id for n in workflow.graph.nodes}
            assert workflow.graph.entry in node_ids


def test_bfs_workflows_and_alias():
    assert resolve_domain_id("banking") == "bfs"
    bfs = get_domain("banking")
    assert {w.id for w in bfs.workflows} == {"afi", "clu", "rca"}
    assert get_workflow("bfs", "fraud").id == "afi"


def test_workflows_have_mcp_evals_and_skills():
    for domain in load_domains():
        assert domain.mcp_servers
        for workflow in domain.workflows:
            assert workflow.skills
            assert workflow.tools
            assert workflow.evals


def test_recommended_stacks_match_plan():
    expected = {
        ("bfs", "afi"): ("litellm", "redis", "memory"),
        ("bfs", "clu"): ("litellm", "memory", "opensearch"),
        ("bfs", "rca"): ("openai", "memory", "memory"),
        ("hcls", "epa"): ("litellm", "redis", "memory"),
        ("hcls", "ctpm"): ("litellm", "memory", "qdrant"),
        ("hcls", "addw"): ("ollama", "memory", "memory"),
        ("retail", "accr"): ("litellm", "memcached", "memory"),
        ("retail", "dcap"): ("litellm", "redis", "memory"),
        ("retail", "avmts"): ("litellm", "memory", "opensearch"),
    }
    for (domain, workflow), (gateway, cache, vector) in expected.items():
        stack = get_workflow(domain, workflow).recommended_stack
        assert (stack.gateway, stack.cache, stack.vector) == (gateway, cache, vector)
