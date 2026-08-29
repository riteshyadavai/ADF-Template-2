"""Non-interactive init tests."""

from pathlib import Path

from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()

REQUIRED = (
    "app",
    "agents",
    "factories",
    "config",
    "shared",
    "tests",
    "evals",
    "docs",
    "examples",
    "deployment",
)


def test_init_dry_run_writes_nothing(tmp_path: Path):
    dest = tmp_path / "demo"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "demo",
            "--output",
            str(dest),
            "--domain",
            "baking",
            "--workflow",
            "allergen_compliance",
            "--yes",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Dry run" in result.output
    assert not dest.exists()


def test_init_yes_copies_full_tree_and_one_workflow(tmp_path: Path):
    dest = tmp_path / "hospital-prior-auth"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "hospital-prior-auth",
            "--output",
            str(dest),
            "--domain",
            "healthcare",
            "--workflow",
            "prior_auth",
            "--gateway",
            "litellm",
            "--cache",
            "memory",
            "--vector",
            "opensearch",
            "--opensearch-url",
            "http://localhost:9200",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    for name in REQUIRED:
        assert (dest / name).is_dir(), name
    assert (dest / "factories" / "cache" / "memcached").is_dir()
    assert (dest / "factories" / "cache" / "redis").is_dir()
    wf = dest / "domains" / "healthcare" / "workflows"
    assert (wf / "prior_auth" / "graph.yaml").exists()
    assert (wf / "prior_auth" / "agents" / "prior_auth_intake.yaml").exists()
    assert not (wf / "claims").exists()
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "CACHE_BACKEND=memory" in env
    assert "VECTOR_BACKEND=opensearch" in env
    assert "VECTOR_OPENSEARCH_URL=http://localhost:9200" in env
    project = (dest / "config" / "project.yaml").read_text(encoding="utf-8")
    assert "domain: healthcare" in project
    assert "workflow: prior_auth" in project
    assert "template_version:" in project
    assert (dest / "factory-choices.json").exists()
    pyproject = (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "hospital-prior-auth"' in pyproject


def test_list_domains():
    result = runner.invoke(app, ["list-domains"])
    assert result.exit_code == 0
    assert "banking" in result.output
    assert "healthcare" in result.output


def test_list_workflows_banking():
    result = runner.invoke(app, ["list-workflows", "--domain", "banking"])
    assert result.exit_code == 0
    assert "kyc" in result.output
    assert "fraud" in result.output


def test_list_factories():
    result = runner.invoke(app, ["list-factories"])
    assert result.exit_code == 0
    assert "cache" in result.output
    assert "qdrant" in result.output


def test_init_dry_run_qdrant_env(tmp_path: Path):
    dest = tmp_path / "qdemo"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "qdemo",
            "--output",
            str(dest),
            "--domain",
            "banking",
            "--workflow",
            "kyc",
            "--vector",
            "qdrant",
            "--yes",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "VECTOR_BACKEND=qdrant" in result.output
