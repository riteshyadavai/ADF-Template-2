"""Copy the bundled template and apply init renders."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from cli.catalog import CatalogWorkflow, materialize_workflow
from cli.choices import FactoryChoices
from cli.template_root import template_root

IGNORE_DIR_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cursor",
    "node_modules",
    "dist",
    "htmlcov",
    ".tox",
    "site",
}
IGNORE_FILE_NAMES = {".env", "uv.lock", ".coverage"}
# When the CLI is installed via `uv tool`, template_root() is site-packages.
# Only copy the template snapshot — never aiohttp, boto3, *.dist-info, etc.
TEMPLATE_TOP_LEVEL = frozenset(
    {
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
        "data",
        "notebooks",
        "Makefile",
        "README.md",
        ".env.example",
        "Dockerfile",
        "LICENSE",
        "pyproject.toml",
        "mkdocs.yml",
    }
)
REQUIRED_DIRS = (
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


def should_skip(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    if any(part in IGNORE_DIR_NAMES for part in rel_parts):
        return True
    if path.name in IGNORE_FILE_NAMES:
        return True
    if path.suffix in {".pyc", ".pyo", ".so"}:
        return True
    if any(part.endswith(".dist-info") or part.endswith(".egg-info") for part in rel_parts):
        return True
    if rel_parts[0] not in TEMPLATE_TOP_LEVEL:
        return True
    return False


def planned_copy_paths(src: Path) -> list[Path]:
    paths: list[Path] = []
    for item in src.rglob("*"):
        if should_skip(item, src):
            continue
        if item.is_file():
            paths.append(item)
    return paths


def copy_template(src: Path, dest: Path) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for item in planned_copy_paths(src):
        rel = item.relative_to(src)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        written.append(str(rel))
    return written


def assert_required_dirs(dest: Path) -> None:
    missing = [name for name in REQUIRED_DIRS if not (dest / name).is_dir()]
    if missing:
        raise RuntimeError(f"Copy incomplete; missing directories: {', '.join(missing)}")


def render_project_files(dest: Path, choices: FactoryChoices) -> None:
    pyproject = dest / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
        text = text.replace(
            'name = "multi-agent-factory"',
            f'name = "{choices.project_name}"',
            1,
        )
        text = text.replace(
            '[project.scripts]\n'
            '66degrees-factory = "cli.main:app"\n'
            'factory = "cli.main:app"\n\n',
            "",
            1,
        )
        text = text.replace(
            'packages = ["agents", "app", "shared", "factories", "config", "cli"]',
            'packages = ["agents", "app", "shared", "factories", "config"]',
            1,
        )
        text = text.replace('"catalogs" = "catalogs"\n', "")
        pyproject.write_text(text, encoding="utf-8")

    (dest / "README.md").write_text(choices.render_readme(), encoding="utf-8")
    (dest / ".env").write_text(choices.render_env(), encoding="utf-8")
    (dest / "config" / "app.yaml").write_text(choices.render_app_yaml(), encoding="utf-8")
    eval_dir = dest / "evals" / choices.workflow
    eval_dir.mkdir(parents=True, exist_ok=True)
    (eval_dir / "app.evalset.json").write_text(
        json.dumps(choices.render_evalset(), indent=2) + "\n",
        encoding="utf-8",
    )
    choices.write_choices_file(dest)


def generate_project(choices: FactoryChoices, *, dry_run: bool = False) -> list[str]:
    src = template_root()
    dest = choices.dest()
    files = [str(p.relative_to(src)) for p in planned_copy_paths(src)]
    workflow_rel = f"domains/{choices.domain}/workflows/{choices.workflow}/"
    if dry_run:
        return [*files, workflow_rel, ".env", "config/app.yaml", "factory-choices.json"]

    if dest.exists() and any(dest.iterdir()) and dest.resolve() != src.resolve():
        raise FileExistsError(f"Destination is not empty: {dest} (pass --force to overwrite)")

    if dest.resolve() == src.resolve():
        raise ValueError("Refusing to init into the template source directory")

    copy_template(src, dest)
    assert_required_dirs(dest)
    render_project_files(dest, choices)
    plan = None
    if choices.workflow_plan:
        plan = CatalogWorkflow.model_validate(choices.workflow_plan)
    materialize_workflow(
        dest,
        choices.domain,
        choices.workflow,
        mcp_examples=choices.mcp_examples,
        catalog_root=src,
        workflow=plan,
    )
    return [*files, workflow_rel]


def destination_exists_nonempty(path: Path) -> bool:
    return path.exists() and any(path.iterdir())
