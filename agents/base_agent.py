"""Main orchestrator — configurable workflow engine with HITL and run traces."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from uuid import uuid4

from agents.prompts.registry import PromptRegistry
from agents.registry import AgentRegistry
from agents.security.audit_log import AuditLog
from agents.security.execution_policies import ExecutionPolicyContext, ExecutionPolicyEngine
from factories.ai_gateway.protocol import LLMGateway, LLMMessage, LLMRequest
from shared.errors import HITLRequiredError
from shared.logger import bind_request_context, get_logger
from shared.metrics import AGENT_RUNS
from shared.run_record import RunRecord, RunStep, RunStepType
from shared.schemas import AgentRequest, AgentResponse

log = get_logger(__name__)

HITLCallback = Callable[[RunRecord, str], Awaitable[str | None]]


class WorkflowState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED_HITL = "paused_hitl"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowNode:
    id: str
    agent_name: str | None = None
    requires_hitl: bool = False
    next_nodes: list[str] = field(default_factory=list)


@dataclass
class WorkflowGraph:
    entry_node: str
    nodes: dict[str, WorkflowNode]
    hitl_nodes: set[str] = field(default_factory=set)


class Orchestrator:
    """Entry point: routing, planning, coordination, execution."""

    def __init__(
        self,
        *,
        gateway: LLMGateway,
        agent_registry: AgentRegistry,
        prompt_registry: PromptRegistry,
        execution_policies: ExecutionPolicyEngine | None = None,
        audit_log: AuditLog | None = None,
        workflow: WorkflowGraph | None = None,
    ) -> None:
        self._gateway = gateway
        self._agents = agent_registry
        self._prompts = prompt_registry
        self._execution_policies = execution_policies or ExecutionPolicyEngine()
        self._audit = audit_log or AuditLog()
        self._workflow = workflow or self._default_workflow()
        self._hitl_callback: HITLCallback | None = None
        self._paused_runs: dict[str, RunRecord] = {}

    def _default_workflow(self) -> WorkflowGraph:
        return WorkflowGraph(
            entry_node="respond",
            nodes={"respond": WorkflowNode(id="respond")},
        )

    def set_hitl_callback(self, callback: HITLCallback) -> None:
        self._hitl_callback = callback

    async def run(self, request: AgentRequest) -> AgentResponse:
        run_id = uuid4()
        correlation_id = request.idempotency_key or str(run_id)
        bind_request_context(
            correlation_id=correlation_id,
            tenant_id=request.tenant_id,
            run_id=str(run_id),
        )

        record = RunRecord(
            correlation_id=correlation_id,
            trace_id=correlation_id,
            tenant_id=request.tenant_id,
            session_id=request.session_id,
            user_query=request.query,
        )

        plan_step = RunStep(step_type=RunStepType.PLAN, name="orchestrator_plan")
        record.add_step(plan_step)

        try:
            self._execution_policies.check(
                ExecutionPolicyContext(
                    agent_name="orchestrator",
                    action="run",
                    tools=[],
                    estimated_cost_usd=0.01,
                    tenant_id=request.tenant_id,
                    metadata=request.metadata,
                )
            )

            output = await self._execute_workflow(record, request)
            record.complete(output)

            self._audit.append(
                event_type="agent_run",
                actor=request.user_id,
                action="complete",
                resource="orchestrator",
                tenant_id=request.tenant_id,
                run_id=str(record.run_id),
            )
            AGENT_RUNS.labels(tenant_id=request.tenant_id, status="success").inc()

            return AgentResponse(
                run_id=record.run_id,
                output=output,
                session_id=request.session_id,
                cost_usd=record.total_cost_usd,
                token_usage={"total": record.total_tokens},
            )
        except HITLRequiredError:
            self._paused_runs[str(record.run_id)] = record
            record.status = WorkflowState.PAUSED_HITL.value
            AGENT_RUNS.labels(tenant_id=request.tenant_id, status="paused").inc()
            raise
        except Exception as exc:
            record.fail(str(exc))
            AGENT_RUNS.labels(tenant_id=request.tenant_id, status="failed").inc()
            log.error("orchestrator_failed", error=str(exc))
            raise

    async def resume(self, run_id: str, approval: str) -> AgentResponse:
        record = self._paused_runs.pop(run_id, None)
        if record is None:
            raise ValueError(f"No paused run found: {run_id}")

        hitl_step = RunStep(
            step_type=RunStepType.HITL,
            name="human_approval",
            output_summary=approval,
        )
        record.add_step(hitl_step)

        request = AgentRequest(
            query=record.user_query or "",
            session_id=record.session_id or str(uuid4()),
            tenant_id=record.tenant_id,
        )
        output = await self._execute_workflow(record, request, skip_to="respond")
        record.complete(output)
        return AgentResponse(
            run_id=record.run_id,
            output=output,
            session_id=request.session_id,
            cost_usd=record.total_cost_usd,
        )

    async def _execute_workflow(
        self,
        record: RunRecord,
        request: AgentRequest,
        skip_to: str | None = None,
    ) -> str:
        current: str | None = skip_to or self._workflow.entry_node

        while current:
            node = self._workflow.nodes[current]

            if node.requires_hitl or current in self._workflow.hitl_nodes:
                if self._hitl_callback is None:
                    raise HITLRequiredError(f"HITL required at node '{current}'")
                approval = await self._hitl_callback(record, current)
                if approval is None:
                    raise HITLRequiredError(f"Awaiting approval at node '{current}'")

            if node.agent_name:
                contract = self._agents.get(node.agent_name)
                prompt = self._prompts.load(contract.name, contract.prompt_version)
                step = RunStep(
                    step_type=RunStepType.SUB_AGENT,
                    name=contract.name,
                    input_summary=request.query[:200],
                )
                record.add_step(step)

                llm_response = await self._gateway.complete(
                    LLMRequest(
                        messages=[
                            LLMMessage(role="system", content=prompt),
                            LLMMessage(role="user", content=request.query),
                        ],
                        tenant_id=request.tenant_id,
                        run_id=str(record.run_id),
                        bypass_cache=request.bypass_cache,
                    )
                )
                step.output_summary = llm_response.content[:200]
                step.token_usage = llm_response.token_usage
                step.cost_usd = llm_response.cost_usd
                step.ended_at = step.started_at

                llm_step = RunStep(
                    step_type=RunStepType.LLM,
                    name=llm_response.model,
                    token_usage=llm_response.token_usage,
                    cost_usd=llm_response.cost_usd,
                    parent_step_id=step.step_id,
                )
                record.add_step(llm_step)
                return llm_response.content

            current = node.next_nodes[0] if node.next_nodes else None

        system_prompt = self._prompts.load("orchestrator", "latest")
        response = await self._gateway.complete(
            LLMRequest(
                messages=[
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(role="user", content=request.query),
                ],
                tenant_id=request.tenant_id,
                run_id=str(record.run_id),
            )
        )
        return response.content
