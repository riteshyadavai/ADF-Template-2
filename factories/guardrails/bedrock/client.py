"""AWS Bedrock content guardrail implementation."""

from __future__ import annotations

import asyncio
import importlib
from typing import Any

from factories.guardrails.protocol import ContentGuardrail, GuardrailResult


class BedrockContentGuardrail(ContentGuardrail):
    def __init__(self, region: str, guardrail_id: str, guardrail_version: str) -> None:
        self._region = region
        self._guardrail_id = guardrail_id
        self._guardrail_version = guardrail_version
        self._client: Any | None = None

    def _runtime_client(self) -> Any:
        if self._client is None:
            try:
                boto3 = importlib.import_module("boto3")
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "Bedrock Guardrails requires the optional 'aws' dependencies. "
                    "Install them with: uv sync --extra aws"
                ) from exc
            self._client = boto3.client("bedrock-runtime", region_name=self._region)
        return self._client

    async def check_input(self, text: str) -> GuardrailResult:
        return await self._apply("INPUT", [{"text": {"text": text}}])

    async def check_output(
        self,
        text: str,
        *,
        source_documents: list[str] | None = None,
        query: str = "",
    ) -> GuardrailResult:
        content = [
            {"text": {"text": source, "qualifiers": ["grounding_source"]}}
            for source in source_documents or []
            if source.strip()
        ]
        if query:
            content.append({"text": {"text": query, "qualifiers": ["query"]}})
        content.append({"text": {"text": text, "qualifiers": ["guard_content"]}})
        return await self._apply("OUTPUT", content)

    async def _apply(self, source: str, content: list[dict[str, Any]]) -> GuardrailResult:
        def invoke() -> dict[str, Any]:
            return self._runtime_client().apply_guardrail(
                guardrailIdentifier=self._guardrail_id,
                guardrailVersion=self._guardrail_version,
                source=source,
                content=content,
            )

        response = await asyncio.to_thread(invoke)
        action = response.get("action", "NONE")
        outputs = [
            block["text"]
            for block in response.get("outputs", [])
            if isinstance(block.get("text"), str)
        ]
        reasons = self._blocked_reasons(response)
        return GuardrailResult(
            allowed=action == "NONE" or not reasons,
            action=action,
            reason="; ".join(reasons) if reasons else "Content passed all guardrail checks",
            outputs=outputs,
        )

    @staticmethod
    def _blocked_reasons(response: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        for assessment in response.get("assessments", []):
            for topic in assessment.get("topicPolicy", {}).get("topics", []):
                if topic.get("action") == "BLOCKED":
                    reasons.append(f"topic_blocked:{topic.get('name', 'unknown')}")
            for item in assessment.get("contentPolicy", {}).get("filters", []):
                if item.get("action") == "BLOCKED":
                    reasons.append(f"content_blocked:{item.get('type', 'unknown')}")
            for entity in assessment.get("sensitiveInformationPolicy", {}).get(
                "piiEntities", []
            ):
                if entity.get("action") == "BLOCKED":
                    reasons.append(f"pii_blocked:{entity.get('type', 'unknown')}")
            for item in assessment.get("contextualGroundingPolicy", {}).get("filters", []):
                if item.get("action") == "BLOCKED":
                    reasons.append(f"grounding_blocked:{item.get('type', 'unknown')}")
        return reasons
