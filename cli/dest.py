"""Where init writes: this folder vs a new folder vs refuse the template."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from cli.copier import destination_exists_nonempty
from cli.template_root import template_root


@dataclass(frozen=True)
class DestSuggestion:
    project_name: str
    output: Path
    mode: str  # this_folder | new_folder | factory_repo
    cwd: Path
    cwd_empty: bool
    is_template: bool


def slugify(name: str) -> str:
    return name.replace("-", "_").replace(" ", "_")


def dest_mode_label(dest: Path, cwd: Path | None = None) -> str:
    here = (cwd or Path.cwd()).resolve()
    return "this folder" if dest.expanduser().resolve() == here else "new folder"


def suggest_dest(
    *,
    cwd: Path | None = None,
    template: Path | None = None,
    name: str | None = None,
    output: Path | None = None,
) -> DestSuggestion:
    here = (cwd or Path.cwd()).resolve()
    root = (template or template_root()).resolve()
    is_template = here == root
    cwd_empty = here.is_dir() and not destination_exists_nonempty(here)

    if output is not None:
        dest = output.expanduser()
        project_name = name or dest.name or here.name or "my-agent-project"
        if dest.resolve() == here:
            mode = "factory_repo" if is_template else "this_folder"
        else:
            mode = "new_folder"
        return DestSuggestion(project_name, dest, mode, here, cwd_empty, is_template)

    if is_template:
        project_name = name or "my-agent-project"
        dest = Path.home() / "Desktop" / project_name
        return DestSuggestion(project_name, dest, "factory_repo", here, cwd_empty, True)

    if cwd_empty:
        project_name = name or here.name or "my-agent-project"
        return DestSuggestion(project_name, here, "this_folder", here, True, False)

    project_name = name or "my-agent-project"
    dest = here / project_name
    return DestSuggestion(project_name, dest, "new_folder", here, False, False)
