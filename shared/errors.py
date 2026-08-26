"""Platform exception hierarchy."""


class FactoryError(Exception):
    """Base exception for all factory errors."""


class AgentNotFoundError(FactoryError):
    """Raised when a requested agent is not registered."""


class AgentContractError(FactoryError):
    """Raised when an agent manifest fails validation."""


class MCPPermissionError(FactoryError):
    """Raised when an agent attempts to use a disallowed MCP tool."""


class BudgetExceededError(FactoryError):
    """Raised when token or cost budget is exceeded."""


class GuardrailViolationError(FactoryError):
    """Raised when a guardrail policy blocks an action."""


class HITLRequiredError(FactoryError):
    """Raised when human-in-the-loop approval is required."""


class IdempotencyConflictError(FactoryError):
    """Raised when an idempotency key is reused with different payload."""
