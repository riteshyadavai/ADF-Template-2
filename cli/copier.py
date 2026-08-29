"""Copy the bundled template and apply init renders."""

from __future__ import annotations

import shutil
from pathlib import Path

from cli.catalog import materialize_workflow
from cli.choices import FactoryChoices
from cli.template_root import template_root
from config.project_config import ProjectConfig, dump_project_config

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
}
IGNORE_FILE_NAMES = {".env", "uv.lock", ".coverage"}
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
    if path.suffix in {".pyc", ".pyo"}:
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
        pyproject.write_text(text, encoding="utf-8")

    readme = dest / "README.md"
    if readme.exists():
        body = readme.read_text(encoding="utf-8")
        pair = f"{choices.domain}/{choices.workflow}"
        header = f"# {choices.project_name}\n\nGenerated from 66degrees-factory ({pair}).\n\n"
        if body.startswith("# "):
            rest = body.split("\n", 1)[1] if "\n" in body else ""
            readme.write_text(header + rest, encoding="utf-8")
        else:
            readme.write_text(header + body, encoding="utf-8")

    (dest / ".env").write_text(choices.render_env(), encoding="utf-8")

    overlay = dest / "config" / "environments" / f"{choices.environment}.yaml"
    if overlay.exists() and choices.environment == "local":
        text = overlay.read_text(encoding="utf-8")
        if "cache:\n  backend:" in text:
            text = text.replace(
                "cache:\n  backend: memory",
                f"cache:\n  backend: {choices.cache}",
            )
            overlay.write_text(text, encoding="utf-8")

    project = ProjectConfig(
        domain=choices.domain,
        workflow=choices.workflow,
        template_package=choices.template_package,
        template_version=choices.template_version,
    )
    (dest / "config" / "project.yaml").write_text(dump_project_config(project), encoding="utf-8")
    choices.write_choices_file(dest)


def generate_project(choices: FactoryChoices, *, dry_run: bool = False) -> list[str]:
    src = template_root()
    dest = choices.dest()
    files = [str(p.relative_to(src)) for p in planned_copy_paths(src)]
    workflow_rel = f"domains/{choices.domain}/workflows/{choices.workflow}/"
    if dry_run:
        return [*files, workflow_rel, ".env", "config/project.yaml", "factory-choices.json"]

    if dest.exists() and any(dest.iterdir()) and dest.resolve() != src.resolve():
        raise FileExistsError(f"Destination is not empty: {dest} (pass --force to overwrite)")

    if dest.resolve() == src.resolve():
        raise ValueError("Refusing to init into the template source directory")

    copy_template(src, dest)
    assert_required_dirs(dest)
    render_project_files(dest, choices)
    materialize_workflow(
        dest,
        choices.domain,
        choices.workflow,
        mcp_examples=choices.mcp_examples,
        catalog_root=src,
    )
    return [*files, workflow_rel]


def destination_exists_nonempty(path: Path) -> bool:
    return path.exists() and any(path.iterdir())
