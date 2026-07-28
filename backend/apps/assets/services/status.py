"""Asset status transition rules (lifecycle state machine)."""

from __future__ import annotations

from assets.models import Asset

Status = Asset.Status

# From → allowed next statuses. Empty set = terminal (except LOST → AVAILABLE if recovered).
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    Status.AVAILABLE: {
        Status.REQUESTED,
        Status.ALLOCATED,
        Status.MAINTENANCE,
        Status.RETIRED,
        Status.LOST,
    },
    Status.REQUESTED: {
        Status.AVAILABLE,
        Status.ALLOCATED,
        Status.MAINTENANCE,
    },
    Status.ALLOCATED: {
        Status.AVAILABLE,
        Status.MAINTENANCE,
        Status.LOST,
        Status.RETIRED,
    },
    Status.MAINTENANCE: {
        Status.AVAILABLE,
        Status.ALLOCATED,
        Status.RETIRED,
        Status.LOST,
    },
    Status.RETIRED: set(),
    Status.LOST: {Status.AVAILABLE},
}


def can_transition(current: str, new: str) -> bool:
    if current == new:
        return True
    return new in ALLOWED_TRANSITIONS.get(current, set())


def assert_transition(current: str, new: str) -> None:
    """Raise ValueError if the transition is illegal."""
    if can_transition(current, new):
        return
    allowed = ", ".join(sorted(ALLOWED_TRANSITIONS.get(current, set()))) or "(none)"
    raise ValueError(
        f"Cannot change status from {current} to {new}. Allowed: {allowed}."
    )
