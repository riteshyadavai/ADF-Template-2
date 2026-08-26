# ruff: noqa: B008

"""Generic agent run API."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse

from agents.security.authn import get_current_user
from app.platform import Platform, get_platform
from app.schemas import CostReportResponse, ResumeRequest, RunAgentRequest, RunAgentResponse
from shared.errors import HITLRequiredError
from shared.schemas import AgentRequest

router = APIRouter()


def _platform() -> Platform:
    return get_platform()


@router.post("/agents/run", response_model=RunAgentResponse, status_code=status.HTTP_200_OK)
async def run_agent(
    body: RunAgentRequest,
    user: dict = Depends(get_current_user),
    platform: Platform = Depends(_platform),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
) -> RunAgentResponse:
    if idempotency_key:
        cached = platform.idempotency.get(idempotency_key)
        if cached:
            return RunAgentResponse(**cached)

    request = AgentRequest(
        query=body.query,
        session_id=body.session_id or str(uuid4()),
        user_id=user.get("sub", "anonymous"),
        tenant_id=tenant_id,
        idempotency_key=idempotency_key,
        bypass_cache=body.bypass_cache,
        metadata=body.metadata,
    )

    try:
        result = await platform.orchestrator.run(request)
    except HITLRequiredError as exc:
        raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail=str(exc)) from exc

    response = RunAgentResponse(
        run_id=result.run_id,
        output=result.output,
        session_id=result.session_id,
        cost_usd=result.cost_usd,
        token_usage=result.token_usage,
    )

    if idempotency_key:
        platform.idempotency.set(idempotency_key, response.model_dump(mode="json"))

    return response


@router.post("/agents/run/stream")
async def run_agent_stream(
    body: RunAgentRequest,
    user: dict = Depends(get_current_user),
    platform: Platform = Depends(_platform),
    tenant_id: str = Header(default="default", alias="X-Tenant-ID"),
) -> StreamingResponse:
    async def event_stream():
        request = AgentRequest(
            query=body.query,
            session_id=body.session_id or str(uuid4()),
            user_id=user.get("sub", "anonymous"),
            tenant_id=tenant_id,
            bypass_cache=body.bypass_cache,
        )
        result = await platform.orchestrator.run(request)
        yield result.output

    return StreamingResponse(event_stream(), media_type="text/plain")


@router.post("/agents/runs/{run_id}/resume", response_model=RunAgentResponse)
async def resume_run(
    run_id: str,
    body: ResumeRequest,
    user: dict = Depends(get_current_user),
    platform: Platform = Depends(_platform),
) -> RunAgentResponse:
    result = await platform.orchestrator.resume(run_id, body.approval)
    return RunAgentResponse(
        run_id=result.run_id,
        output=result.output,
        session_id=result.session_id,
        cost_usd=result.cost_usd,
        token_usage=result.token_usage,
    )


@router.get("/costs/{tenant_id}", response_model=CostReportResponse)
async def get_costs(
    tenant_id: str,
    user: dict = Depends(get_current_user),
    platform: Platform = Depends(_platform),
) -> CostReportResponse:
    spend = platform.factories.ai_gateway().get_spend(tenant_id)
    return CostReportResponse(
        tenant_id=tenant_id,
        daily_spend_usd=spend["daily"],
        monthly_spend_usd=spend["monthly"],
    )
