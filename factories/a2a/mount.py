"""Mount A2A routes on a FastAPI (Starlette) app."""

from __future__ import annotations

from fastapi import FastAPI

from factories.a2a.protocol import A2AServerBundle


def mount_a2a(app: FastAPI, bundle: A2AServerBundle) -> None:
    for route in bundle.routes:
        app.router.routes.append(route)
