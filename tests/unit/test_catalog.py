"""Catalog schema tests."""

from cli.catalog import load_domains


def test_all_domain_catalogs_validate():
    domains = load_domains()
    ids = {d.id for d in domains}
    assert ids == {"baking", "banking", "healthcare", "insurance", "retail"}
    for domain in domains:
        assert domain.workflows
        seen = set()
        for workflow in domain.workflows:
            assert workflow.id not in seen
            seen.add(workflow.id)
            assert workflow.agents
            node_ids = {n.id for n in workflow.graph.nodes}
            assert workflow.graph.entry in node_ids


def test_banking_has_expected_workflows():
    banking = next(d for d in load_domains() if d.id == "banking")
    assert {w.id for w in banking.workflows} == {
        "kyc",
        "fraud",
        "loan_origination",
        "compliance",
    }
