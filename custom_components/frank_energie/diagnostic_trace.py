"""Bounded, privacy-safe in-memory source evidence for diagnostic exports.

Never store API payloads, identifiers, request paths, exception messages or
energy/financial amounts. Evidence resets at HA integration restart and does
not cause any extra API requests.
"""

from __future__ import annotations

from collections import deque
from datetime import UTC, date, datetime
from typing import Any, Final

_ALLOWED_SOURCES: Final[frozenset[str]] = frozenset(
    {
        "public_market",
        "customer_tariff",
        "price_selection",
        "month_summary",
        "invoices",
        "period_usage",
        "month_insights",
    }
)

_ALLOWED_OUTCOMES: Final[frozenset[str]] = frozenset(
    {
        "present",
        "empty",
        "not_published",
        "skipped_unauthenticated",
        "skipped_missing_site",
        "api_error",
        "network_error",
        "auth_error",
        "public_fallback",
        "customer",
        "mixed",
        "public",
        "cached_fallback",
        "not_available",
    }
)


class DiagnosticTrace:
    """Record source outcomes for a single runtime coordinator, bounded to 24."""

    def __init__(self) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=24)

    def record(
        self,
        source: str,
        outcome: str,
        *,
        period: date | str | None = None,
        electricity_slots: int | None = None,
        gas_slots: int | None = None,
        error: BaseException | None = None,
    ) -> None:
        """Append only predefined, non-identifying fields."""
        if source not in _ALLOWED_SOURCES or outcome not in _ALLOWED_OUTCOMES:
            raise ValueError("Unknown diagnostic evidence category")

        if isinstance(period, date):
            safe_period = period.isoformat()
        elif isinstance(period, str):
            # Only a calendar month YYYY-MM or ISO date YYYY-MM-DD.
            from datetime import date as date_type

            safe_period = None
            if len(period) == 7:
                try:
                    date_type.fromisoformat(period + "-01")
                    safe_period = period
                except ValueError:
                    pass
            elif len(period) == 10:
                try:
                    date_type.fromisoformat(period)
                    safe_period = period
                except ValueError:
                    pass
        else:
            safe_period = None

        event: dict[str, Any] = {
            "at_utc": datetime.now(UTC).isoformat(),
            "source": source,
            "outcome": outcome,
        }
        if safe_period:
            event["period"] = safe_period
        for key, value in (
            ("electricity_slots", electricity_slots),
            ("gas_slots", gas_slots),
        ):
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                event[key] = value
        if error is not None:
            # Class only: str(error) may contain tokens, GraphQL variables,
            # addresses, connection identifiers, or other customer data.
            event["error_class"] = type(error).__name__
        self._events.append(event)

    def snapshot(self) -> dict[str, Any]:
        """Return a detached bounded snapshot, oldest to newest."""
        events = [dict(event) for event in self._events]
        latest: dict[str, dict[str, Any]] = {}
        for event in events:
            latest[event["source"]] = event
        return {
            "retention": "last_24_events_in_memory_since_restart",
            "events": events,
            "latest_by_source": latest,
        }
