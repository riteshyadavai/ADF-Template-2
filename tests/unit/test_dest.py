"""Init destination suggestions."""

from pathlib import Path

from cli.dest import dest_mode_label, suggest_dest
from cli.ui import stack_one_liner


def test_empty_cwd_inits_this_folder(tmp_path: Path):
    empty = tmp_path / "demo-afi"
    empty.mkdir()
    suggestion = suggest_dest(cwd=empty, template=tmp_path / "factory")
    assert suggestion.mode == "this_folder"
    assert suggestion.project_name == "demo-afi"
    assert suggestion.output == empty.resolve()
    assert dest_mode_label(suggestion.output, cwd=empty) == "this folder"


def test_factory_repo_never_suggests_dot(tmp_path: Path):
    factory = tmp_path / "factory"
    factory.mkdir()
    suggestion = suggest_dest(cwd=factory, template=factory, name="demo")
    assert suggestion.mode == "factory_repo"
    assert suggestion.is_template
    assert suggestion.output != factory.resolve()
    assert suggestion.output.name == "demo"


def test_nonempty_cwd_suggests_subfolder(tmp_path: Path):
    here = tmp_path / "work"
    here.mkdir()
    (here / "readme.txt").write_text("x\n", encoding="utf-8")
    suggestion = suggest_dest(cwd=here, template=tmp_path / "factory", name="demo")
    assert suggestion.mode == "new_folder"
    assert suggestion.output == here / "demo"


def test_backend_label_marks_current():
    from cli.factory_catalog import backend_id_from_label, labeled_backend_choices

    labels = labeled_backend_choices("cache", current="redis")
    current = next(label for label in labels if "redis" in label and label.startswith("●"))
    assert backend_id_from_label(current) == "redis"
    memory = next(label for label in labels if backend_id_from_label(label) == "memory")
    assert memory.startswith("  ")


def test_questionary_style_is_valid():
    import questionary
    from prompt_toolkit.styles import Style as PTStyle

    from cli.catalog import get_workflow
    from cli.ui import print_plan_card, questionary_style

    style = questionary_style()
    assert isinstance(style, PTStyle)
    questionary.select("probe", choices=["ok"], style=style)
    print_plan_card(get_workflow("bfs", "afi"))


def test_stack_one_liner():
    assert stack_one_liner(gateway="litellm", cache="redis", vector="memory") == (
        "LLM litellm  ·  cache redis  ·  vector memory"
    )
