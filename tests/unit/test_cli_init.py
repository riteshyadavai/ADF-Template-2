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
            "accr",
            "--yes",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Dry run" in result.output
    assert not dest.exists()


def test_init_yes_copies_full_tree_and_one_workflow(tmp_path: Path):
    dest = tmp_path / "hcls-epa"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "hcls-epa",
            "--output",
            str(dest),
            "--domain",
            "healthcare",
            "--workflow",
            "prior authorization",
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
    wf = dest / "domains" / "hcls" / "workflows"
    assert (wf / "epa" / "graph.yaml").exists()
    assert (wf / "epa" / "agents" / "epa_intake.yaml").exists()
    assert not (wf / "ctpm").exists()
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "CACHE_BACKEND=memory" in env
    assert "VECTOR_BACKEND=opensearch" in env
    app_yaml = (dest / "config" / "app.yaml").read_text(encoding="utf-8")
    assert "domain: hcls" in app_yaml
    assert "workflow: epa" in app_yaml
    assert "plan: accepted" in app_yaml
    assert "mcp:" in app_yaml
    assert "hcls-interoperability" in app_yaml
    assert "CoverageRulesEngine" in app_yaml
    readme = (dest / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# hcls-epa")
    assert "list-domains" not in readme
    assert "Artifact Registry" not in readme
    assert "Generate a project" not in readme
    assert (dest / "evals" / "epa" / "app.evalset.json").exists()
    assert not (dest / "config" / "project.yaml").exists()
    assert (dest / "factory-choices.json").exists()
    assert not (dest / "catalogs").exists()
    assert not (dest / "cli").exists()
    pyproject = (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "hcls-epa"' in pyproject
    assert "66degrees-factory" not in pyproject


def test_list_domains():
    result = runner.invoke(app, ["list-domains"])
    assert result.exit_code == 0
    assert "bfs" in result.output
    assert "hcls" in result.output
    assert "retail" in result.output
    assert "other" in result.output


def test_list_workflows_bfs_alias():
    result = runner.invoke(app, ["list-workflows", "--domain", "banking"])
    assert result.exit_code == 0
    assert "afi" in result.output
    assert "clu" in result.output
    assert "rca" in result.output


def test_list_workflows_other():
    result = runner.invoke(app, ["list-workflows", "--domain", "other"])
    assert result.exit_code == 0
    assert "custom" in result.output


def test_list_factories():
    result = runner.invoke(app, ["list-factories"])
    assert result.exit_code == 0
    assert "cache" in result.output
    assert "qdrant" in result.output
    assert "looker" in result.output
    assert "bqml" in result.output


def test_init_yes_looker_bqml(tmp_path: Path):
    dest = tmp_path / "demo-analytics"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "demo-analytics",
            "--output",
            str(dest),
            "--domain",
            "other",
            "--workflow",
            "site_selection",
            "--custom-domain",
            "district_dine",
            "--looker",
            "--bqml",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "LOOKER_ENABLED=true" in env
    assert "LOOKERSDK_CLIENT_ID=CHANGE_ME" in env
    assert "BQML_ENABLED=true" in env
    app_yaml = (dest / "config" / "app.yaml").read_text(encoding="utf-8")
    assert "looker:" in app_yaml
    assert "bqml:" in app_yaml
    assert "enabled: true" in app_yaml


def test_init_yes_default_looker_bqml_off(tmp_path: Path):
    dest = tmp_path / "demo-afi"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "demo-off",
            "--output",
            str(dest),
            "--domain",
            "bfs",
            "--workflow",
            "afi",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "LOOKER_ENABLED=false" in env
    assert "BQML_ENABLED=false" in env


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
            "bfs",
            "--workflow",
            "afi",
            "--vector",
            "qdrant",
            "--yes",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "VECTOR_BACKEND=qdrant" in result.output


def test_init_yes_writes_recommended_stack(tmp_path: Path):
    dest = tmp_path / "demo-afi"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "demo-afi",
            "--output",
            str(dest),
            "--domain",
            "bfs",
            "--workflow",
            "afi",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    app_yaml = (dest / "config" / "app.yaml").read_text(encoding="utf-8")
    assert "domain: bfs" in app_yaml
    assert "workflow: afi" in app_yaml
    assert "backend: redis" in app_yaml
    assert "workflow:" in app_yaml
    assert "afi_intake" in app_yaml
    assert "evals:" in app_yaml
    assert "bfs-operations" in app_yaml
    assert "langfuse:" in app_yaml
    assert "host:" in app_yaml
    assert "hcls:" not in app_yaml
    env = (dest / ".env").read_text(encoding="utf-8")
    assert "CACHE_BACKEND=redis" in env
    assert "GATEWAY_PROVIDER=litellm" in env
    assert "BFS_MCP_TOKEN=CHANGE_ME" in env
    evalset = (dest / "evals" / "afi" / "app.evalset.json").read_text(encoding="utf-8")
    assert "capability" in evalset
    assert "account 4412" in evalset


def test_init_yes_other_custom_slugs(tmp_path: Path):
    dest = tmp_path / "demo-custom"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "demo-custom",
            "--output",
            str(dest),
            "--domain",
            "other",
            "--workflow",
            "intake",
            "--custom-domain",
            "acme",
            "--yes",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (dest / "domains" / "acme" / "workflows" / "intake" / "graph.yaml").exists()
    assert (dest / "domains" / "acme" / "workflows" / "intake" / "agents" / "intake.yaml").exists()
    app_yaml = (dest / "config" / "app.yaml").read_text(encoding="utf-8")
    assert "domain: acme" in app_yaml
    assert "workflow: intake" in app_yaml
    assert "other-operations" in app_yaml
    assert "OTHER_MCP_TOKEN=CHANGE_ME" in (dest / ".env").read_text(encoding="utf-8")
    readme = (dest / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# demo-custom")
    assert "hcls" not in app_yaml


def test_init_yes_other_rejects_invalid_workflow(tmp_path: Path):
    dest = tmp_path / "bad"
    result = runner.invoke(
        app,
        [
            "init",
            "--name",
            "bad",
            "--output",
            str(dest),
            "--domain",
            "other",
            "--workflow",
            "My Flow",
            "--yes",
        ],
    )
    assert result.exit_code != 0
    assert "lowercase slug" in result.output


def test_from_choices_app_yaml(tmp_path: Path):
    src_yaml = tmp_path / "app.yaml"
    src_yaml.write_text(
        "project:\n  domain: bfs\n  workflow: afi\n  plan: accepted\n"
        "cache:\n  backend: memory\n"
        "vector:\n  backend: memory\n",
        encoding="utf-8",
    )
    dest = tmp_path / "replay"
    result = runner.invoke(
        app,
        [
            "init",
            "--from-choices",
            str(src_yaml),
            "--name",
            "replay",
            "--output",
            str(dest),
            "--dry-run",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "bfs" in result.output
    assert "afi" in result.output


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
