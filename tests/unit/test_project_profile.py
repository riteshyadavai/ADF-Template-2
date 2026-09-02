"""app.yaml workflow / MCP / evals readers."""

from pathlib import Path

from config.project_config import load_mcp_servers, load_project_config, load_workflow_evals
from factories.mcp.factory import expand_env_placeholders, make_mcp_bundle


def test_load_project_profile_and_evals(tmp_path: Path):
    config = tmp_path / "config"
    config.mkdir()
    (config / "app.yaml").write_text(
        "project:\n  name: demo\n  domain: bfs\n  workflow: afi\n  skills: [bfs-afi]\n"
        "evals:\n  - id: capability\n    query: hello\n"
        "mcp:\n  servers:\n    - id: bfs-operations\n      enabled: false\n"
        "      transport: streamable_http\n      url: ${BFS_MCP_URL}\n",
        encoding="utf-8",
    )
    project = load_project_config(tmp_path)
    assert project is not None
    assert project.domain == "bfs"
    assert project.skills == ["bfs-afi"]
    evals = load_workflow_evals(tmp_path)
    assert evals[0].id == "capability"
    assert load_mcp_servers(tmp_path)[0]["id"] == "bfs-operations"


def test_mcp_bundle_skips_disabled(tmp_path: Path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir()
    (config / "app.yaml").write_text(
        "mcp:\n  servers:\n    - id: bfs-operations\n      enabled: false\n"
        "      url: ${BFS_MCP_URL}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("config.project_config.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr("config.settings.PROJECT_ROOT", tmp_path)
    bundle = make_mcp_bundle()
    assert bundle.http is None
    assert bundle.stdio is None


def test_expand_env_placeholders(monkeypatch):
    monkeypatch.setenv("BFS_MCP_URL", "https://mcp.example/bfs")
    assert expand_env_placeholders("${BFS_MCP_URL}") == "https://mcp.example/bfs"
