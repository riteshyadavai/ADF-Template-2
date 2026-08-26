"""Unit tests for budget enforcement."""

import pytest

from factories.ai_gateway.litellm.budget import BudgetTracker
from shared.errors import BudgetExceededError


def test_budget_downgrade_when_exceeded():
    tracker = BudgetTracker(daily_limit_usd=1.0, downgrade_model="cheap-model")
    tracker.record_spend("tenant-1", 1.5)
    assert tracker.check_budget("tenant-1") == "cheap-model"


def test_budget_hard_stop_without_downgrade():
    tracker = BudgetTracker(daily_limit_usd=1.0, downgrade_model=None)
    tracker.record_spend("tenant-1", 2.0)
    with pytest.raises(BudgetExceededError):
        tracker.check_budget("tenant-1")
