"""RBAC/ABAC authorization at tool and API level."""

from __future__ import annotations

from fastapi import HTTPException, status


def require_role(user: dict[str, str], allowed: set[str]) -> None:
    role = user.get("role", "user")
    if role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role}' not authorized",
        )


def authorize_tool(user: dict[str, str], tool_name: str, allowed_tools: set[str]) -> None:
    if tool_name not in allowed_tools:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tool '{tool_name}' not authorized for this identity",
        )
