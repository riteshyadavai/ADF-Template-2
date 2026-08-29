"""FastAPI application entry point — HTTP shell only."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app import __version__
from app.platform import get_platform
from app.routes import agents, health
from config.settings import get_settings
from factories.observability.factory import configure_logfire, make_langfuse_tracer
from shared.logger import configure_logging, get_logger
from shared.middleware import CorrelationMiddleware

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    platform = get_platform()
    Path("data").mkdir(exist_ok=True)
    log.info(
        "factory_startup",
        environment=platform.settings.environment.value,
        version=__version__,
        agents=platform.agents.list_agents(),
    )
    yield
    make_langfuse_tracer().shutdown()
    log.info("factory_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationMiddleware)

    app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
    app.include_router(agents.router, prefix=settings.api_prefix, tags=["agents"])

    if settings.a2a.enabled:
        from factories.a2a.executor import OrchestratorAgentExecutor
        from factories.a2a.mount import mount_a2a

        platform = get_platform()

        async def _run_query(text: str) -> str:
            from shared.schemas import AgentRequest

            response = await platform.orchestrator.run(AgentRequest(query=text))
            return response.output

        bundle = platform.factories.a2a_server(OrchestratorAgentExecutor(_run_query))
        if bundle is not None:
            mount_a2a(app, bundle)

    if not configure_logfire(settings, app):
        FastAPIInstrumentor.instrument_app(app)
    return app


app = create_app()


def export_openapi() -> None:
    schema = app.openapi()
    out = Path("dist/openapi.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"OpenAPI schema written to {out}")


def cli() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )


if __name__ == "__main__":
    cli()
