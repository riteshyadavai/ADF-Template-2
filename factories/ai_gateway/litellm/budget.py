"""Per-project/agent budget ceilings with downgrade and hard-stop."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from shared.errors import BudgetExceededError


@dataclass
class BudgetTracker:
    daily_limit_usd: float | None = None
    monthly_limit_usd: float | None = None
    downgrade_model: str | None = None
    _daily_spend: dict[str, float] = field(default_factory=dict)
    _monthly_spend: dict[str, float] = field(default_factory=dict)

    def _day_key(self) -> str:
        return date.today().isoformat()

    def _month_key(self) -> str:
        return date.today().strftime("%Y-%m")

    def record_spend(self, tenant_id: str, cost_usd: float) -> None:
        day = self._day_key()
        month = self._month_key()
        self._daily_spend[f"{tenant_id}:{day}"] = (
            self._daily_spend.get(f"{tenant_id}:{day}", 0.0) + cost_usd
        )
        self._monthly_spend[f"{tenant_id}:{month}"] = (
            self._monthly_spend.get(f"{tenant_id}:{month}", 0.0) + cost_usd
        )

    def check_budget(self, tenant_id: str) -> str | None:
        """Return downgrade model if budget exceeded and downgrade available, else None."""
        day_spend = self._daily_spend.get(f"{tenant_id}:{self._day_key()}", 0.0)
        month_spend = self._monthly_spend.get(f"{tenant_id}:{self._month_key()}", 0.0)

        daily_exceeded = self.daily_limit_usd is not None and day_spend >= self.daily_limit_usd
        monthly_exceeded = (
            self.monthly_limit_usd is not None and month_spend >= self.monthly_limit_usd
        )

        if daily_exceeded or monthly_exceeded:
            if self.downgrade_model:
                return self.downgrade_model
            raise BudgetExceededError(
                f"Budget exceeded for tenant {tenant_id}: "
                f"daily=${day_spend:.4f}, monthly=${month_spend:.4f}"
            )
        return None

    def current_spend(self, tenant_id: str) -> dict[str, float]:
        return {
            "daily": self._daily_spend.get(f"{tenant_id}:{self._day_key()}", 0.0),
            "monthly": self._monthly_spend.get(f"{tenant_id}:{self._month_key()}", 0.0),
        }
