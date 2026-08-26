# ruff: noqa: B008

"""Liveness and readiness."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app import __version__
from app.platform import Platform, get_platform
from shared.schemas import HealthStatus

router = APIRouter()


def _platform() -> Platform:
    return get_platform()


@router.get("/health", response_model=HealthStatus)
async def health(platform: Platform = Depends(_platform)) -> HealthStatus:
    return HealthStatus(
        status="ok",
        version=__version__,
        environment=platform.settings.environment.value,
        checks={"gateway": "ok"},
    )


@router.get("/ready", response_model=HealthStatus)
async def readiness(platform: Platform = Depends(_platform)) -> HealthStatus:
    return HealthStatus(
        status="ready",
        version=__version__,
        environment=platform.settings.environment.value,
    )
