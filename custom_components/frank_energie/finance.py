"""Conservative, source-backed calendar-month finance readings.

Frank's pinned MonthInsights parser silently coerces absent difference amounts
to 0.0. Until that upstream contract is fixed, zero MUST NOT be published as a
verified monthly actual: genuine zero and missing data cannot be distinguished.
This module is intentionally free of Home Assistant and endpoint concerns.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from python_frank_energie.models import MonthInsights

_AMSTERDAM = ZoneInfo("Europe/Amsterdam")


@dataclass(frozen=True, slots=True)
class MonthlyFinanceSnapshot:
    """Period attached to the API result so midnight cannot relabel old data."""

    month: str
    insights: MonthInsights
    retrieved_at: datetime


def month_keys(today: date) -> tuple[str, str]:
    """Current and last *calendar* month, including the January boundary."""
    first = today.replace(day=1)
    return first.strftime("%Y-%m"), (first - timedelta(days=1)).strftime("%Y-%m")


def month_bounds(month: str) -> tuple[date, date] | None:
    """Return [start, exclusive end) for a trusted YYYY-MM month."""
    try:
        start = date.fromisoformat(f"{month}-01")
        if start.strftime("%Y-%m") != month:
            return None
        end = (
            start.replace(year=start.year + 1, month=1)
            if start.month == 12
            else start.replace(month=start.month + 1)
        )
    except (TypeError, ValueError):
        return None
    return start, end


# Each numeric sensor has a *single* source field and a fixed known unit.
# For BE gas the Frank API may report kWh rather than m3: both are separate
# sensors, never silently converted without the calorific conversion factor.
_FIELDS: dict[str, tuple[str | None, str, str | None]] = {
    "electricity_costs": ("electricityDifference", "actualCosts", None),
    "electricity_kwh": ("electricityDifference", "actualUsage", "kwh"),
    "gas_costs": ("gasDifference", "actualCosts", None),
    "gas_kwh": ("gasDifference", "actualUsage", "kwh"),
    "gas_m3": ("gasDifference", "actualUsage", "m3"),
    "feed_in_costs": ("feedInDifference", "actualCosts", None),
    "feed_in_kwh": ("feedInDifference", "actualUsage", "kwh"),
    "expected_total": (None, "expectedCosts", None),
    "expected_electricity": (None, "expectedCostsElectricity", None),
    "expected_gas": (None, "expectedCostsGas", None),
    "expected_fixed": (None, "expectedCostsFixed", None),
    "expected_feed_in": (None, "expectedCostsFeedIn", None),
}


def finance_reading(
    snapshot: MonthlyFinanceSnapshot | None, metric: str
) -> tuple[float | None, str]:
    """Return (value, quality) with a fail-closed source contract."""
    if metric not in _FIELDS:
        raise ValueError(f"Unknown finance metric: {metric}")
    if snapshot is None:
        return None, "not_published"

    bounds = month_bounds(snapshot.month)
    if bounds is None:
        return None, "invalid_period"
    insights = snapshot.insights
    meter_date = getattr(insights, "lastMeterReadingDate", None)
    if not isinstance(meter_date, datetime) or meter_date.tzinfo is None:
        return None, "missing_meter_date"

    # Data for one month may be published on the *first day* of the next.
    # A value read earlier than the requested period is never relabelled.
    start, end = bounds
    local_date = meter_date.astimezone(_AMSTERDAM).date()
    if not start <= local_date <= end:
        return None, "reading_outside_period"

    difference_name, field_name, required_unit = _FIELDS[metric]
    if metric.startswith("gas_") and bool(getattr(insights, "gasExcluded", False)):
        return None, "gas_excluded"

    block = insights if difference_name is None else getattr(insights, difference_name, None)
    if block is None:
        return None, "missing_segment"

    if required_unit is not None:
        actual_unit = getattr(block, "unit", "")
        normalized = str(actual_unit).strip().lower().replace("³", "3")
        if normalized not in (
            {required_unit, "m^3"} if required_unit == "m3" else {required_unit}
        ):
            return None, "unit_mismatch"

    raw = getattr(block, field_name, None)
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None, "missing_value"
    number = float(raw)
    if not math.isfinite(number):
        return None, "invalid_value"

    if number == 0:
        # Difference.from_dict and MonthInsights.from_dict in pinned
        # python-frank-energie==2026.9.20 turn absent numeric fields into 0.
        return None, "zero_unverified_by_client"
    return number, "available"


def finance_attributes(
    snapshot: MonthlyFinanceSnapshot | None, metric: str
) -> dict[str, object]:
    """Keep provenance and quality, never site references or account data."""
    value, quality = finance_reading(snapshot, metric)
    attrs: dict[str, object] = {
        "source": "Frank Energie monthInsights",
        "quality": quality,
        "zero_policy": "withhold_ambiguous_zero",
    }
    if snapshot is None:
        return attrs
    bounds = month_bounds(snapshot.month)
    if bounds is not None:
        attrs["period_start"] = bounds[0].isoformat()
        attrs["period_end_exclusive"] = bounds[1].isoformat()
    attrs["period"] = snapshot.month
    attrs["retrieved_at"] = snapshot.retrieved_at.isoformat()
    meter_date = getattr(snapshot.insights, "lastMeterReadingDate", None)
    if isinstance(meter_date, datetime):
        attrs["last_meter_reading"] = meter_date.isoformat()
    completeness = getattr(snapshot.insights, "meterReadingDayCompleteness", None)
    if isinstance(completeness, (float, int)) and not isinstance(completeness, bool):
        if math.isfinite(completeness):
            attrs["meter_reading_day_completeness"] = completeness
    if metric.startswith("gas_"):
        attrs["gas_excluded"] = bool(getattr(snapshot.insights, "gasExcluded", False))
    if value is not None:
        attrs["value_status"] = "provider_reported"
    return attrs
