"""Immutable append-only audit log for tool calls, model calls, and HITL approvals."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.security.redaction import redact_dict
from config.settings import get_settings


class AuditLog:
    def __init__(self, path: Path | None = None) -> None:
        settings = get_settings()
        self._path = path or Path(settings.security.audit_log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        *,
        event_type: str,
        actor: str,
        action: str,
        resource: str,
        tenant_id: str,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "actor": actor,
            "action": action,
            "resource": resource,
            "tenant_id": tenant_id,
            "run_id": run_id,
            "metadata": redact_dict(metadata or {}),
        }
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
