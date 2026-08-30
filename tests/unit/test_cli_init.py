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
            "retail",
            "--workflow",
            "returns",
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
    assert not (dest / "catalogs").exists()
    assert not (dest / "cli").exists()
    pyproject = (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "hospital-prior-auth"' in pyproject
    assert "66degrees-factory" not in pyproject


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


def test_copy_skips_site_packages_neighbors(tmp_path: Path):
    from cli.copier import copy_template

    src = tmp_path / "site-packages"
    src.mkdir()
    (src / "app").mkdir()
    (src / "app" / "main.py").write_text("# app\n", encoding="utf-8")
    (src / "factories").mkdir()
    (src / "factories" / "ok.py").write_text("# factories\n", encoding="utf-8")
    (src / "pyproject.toml").write_text('[project]\nname = "multi-agent-factory"\n', encoding="utf-8")
    (src / "aiohttp").mkdir()
    (src / "aiohttp" / "__init__.py").write_text("# leak\n", encoding="utf-8")
    (src / "aiohttp-3.14.3.dist-info").mkdir()
    (src / "aiohttp-3.14.3.dist-info" / "METADATA").write_text("Name: aiohttp\n", encoding="utf-8")
    (src / "_cffi_backend.cpython-312-darwin.so").write_bytes(b"\x00")

    dest = tmp_path / "out"
    written = copy_template(src, dest)
    assert "app/main.py" in written
    assert "factories/ok.py" in written
    assert "pyproject.toml" in written
    assert not (dest / "aiohttp").exists()
    assert not (dest / "aiohttp-3.14.3.dist-info").exists()
    assert not (dest / "_cffi_backend.cpython-312-darwin.so").exists()
