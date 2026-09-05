"""Resolve the bundled template root (clone checkout or installed wheel)."""

from __future__ import annotations

from pathlib import Path


def template_root() -> Path:
    root = Path(__file__).resolve().parents[1]
    if (root / "factories").is_dir() and (root / "pyproject.toml").exists():
        return root
    raise FileNotFoundError(
        "Could not locate the factory template (factories/ + pyproject.toml). "
        "Reinstall 66degrees-factory or run from a clone of this repository."
    )


def template_version() -> str:
    try:
        from app import __version__

        return __version__
    except ImportError:
        return "0.2.10"
