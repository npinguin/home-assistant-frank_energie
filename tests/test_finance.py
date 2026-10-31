"""Source-contract regression tests for finance sensors (no live account data)."""

from datetime import date, datetime, UTC
from types import SimpleNamespace

import pytest

from custom_components.frank_energie.finance import (
    MonthlyFinanceSnapshot,
    finance_attributes,
    finance_reading,
    month_bounds,
    month_keys,
)
from python_frank_energie.models import MonthInsights


def _snapshot(
    *,
    month="2026-10",
    electricity_cost=37.5,
    gas_cost=18.1,
    gas_unit="m3",
    gas_excluded=False,
    reading="2026-10-25T13:00:00+00:00",
):
    insights = SimpleNamespace(
        lastMeterReadingDate=datetime.fromisoformat(reading),
        meterReadingDayCompleteness=0.9,
        gasExcluded=gas_excluded,
        electricityDifference=SimpleNamespace(
            actualCosts=electricity_cost, actualUsage=128.5, unit="kWh"
        ),
        gasDifference=SimpleNamespace(
            actualCosts=gas_cost, actualUsage=19.5, unit=gas_unit
        ),
        feedInDifference=SimpleNamespace(
            actualCosts=-5.2, actualUsage=42.3, unit="kWh"
        ),
        expectedCosts=80.0,
        expectedCostsElectricity=49.0,
        expectedCostsGas=22.0,
        expectedCostsFixed=9.0,
        expectedCostsFeedIn=-5.0,
    )
    return MonthlyFinanceSnapshot(
        month=month, insights=insights, retrieved_at=datetime(2026, 10, 26, tzinfo=UTC)
    )


def test_calendar_period_keys_handle_year_boundary():
    assert month_keys(date(2027, 1, 1)) == ("2027-01", "2026-12")
    assert month_bounds("2026-12") == (date(2026, 12, 1), date(2027, 1, 1))
    assert month_bounds("2026-11") == (date(2026, 11, 1), date(2026, 12, 1))
    assert month_bounds("2026-13") is None


@pytest.mark.parametrize(
    ("metric", "expected"),
    [
        ("electricity_costs", 37.5),
        ("electricity_kwh", 128.5),
        ("gas_costs", 18.1),
        ("gas_m3", 19.5),
        ("feed_in_costs", -5.2),
        ("feed_in_kwh", 42.3),
        ("expected_total", 80.0),
        ("expected_electricity", 49.0),
        ("expected_gas", 22.0),
        ("expected_fixed", 9.0),
        ("expected_feed_in", -5.0),
    ],
)
def test_month_insights_fields_are_distinct(metric, expected):
    assert finance_reading(_snapshot(), metric) == (expected, "available")


def test_gas_unit_is_not_silently_converted():
    assert finance_reading(_snapshot(), "gas_kwh") == (None, "unit_mismatch")
    assert finance_reading(_snapshot(gas_unit="kWh"), "gas_kwh") == (
        19.5,
        "available",
    )
    assert finance_reading(_snapshot(gas_unit="kWh"), "gas_m3") == (
        None,
        "unit_mismatch",
    )


def test_missing_or_excluded_gas_never_zero_filled():
    assert finance_reading(_snapshot(gas_excluded=True), "gas_costs") == (
        None,
        "gas_excluded",
    )
    assert finance_reading(None, "gas_costs") == (None, "not_published")


def test_late_meter_reading_must_not_relabel_previous_period():
    assert finance_reading(_snapshot(month="2026-11"), "gas_costs") == (
        None,
        "reading_outside_period",
    )
    # A reading on the first day after the month closes is acceptable.
    assert finance_reading(
        _snapshot(month="2026-09", reading="2026-10-01T00:00:00+02:00"),
        "gas_costs",
    ) == (18.1, "available")


def test_pinned_api_parser_coerces_missing_fields_to_zero_and_is_withheld():
    data = {
        "data": {
            "monthInsights": {
                "_id": "REDACTED",
                "lastMeterReadingDate": "2026-10-25T13:00:00+00:00",
                "gasDifference": {},
                "electricityDifference": {},
                "feedInDifference": {},
            }
        }
    }
    parsed = MonthInsights.from_dict(data)
    assert parsed is not None
    assert parsed.gasDifference.actualCosts == 0
    reading = MonthlyFinanceSnapshot(
        month="2026-10",
        insights=parsed,
        retrieved_at=datetime(2026, 10, 26, tzinfo=UTC),
    )
    assert finance_reading(reading, "gas_costs") == (
        None,
        "zero_unverified_by_client",
    )
    assert finance_reading(reading, "electricity_costs") == (
        None,
        "zero_unverified_by_client",
    )


def test_valid_zero_is_conservatively_withheld_until_client_contract_improves():
    assert finance_reading(_snapshot(electricity_cost=0.0), "electricity_costs") == (
        None,
        "zero_unverified_by_client",
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), True])
def test_invalid_numeric_amounts_are_never_published(value):
    assert (
        finance_reading(_snapshot(electricity_cost=value), "electricity_costs")[0]
        is None
    )


def test_attributes_have_period_quality_and_no_site_or_invoice_identifiers():
    attrs = finance_attributes(_snapshot(), "gas_costs")
    assert attrs["period_start"] == "2026-10-01"
    assert attrs["period_end_exclusive"] == "2026-11-01"
    assert attrs["quality"] == "available"
    assert "site_reference" not in attrs
    assert "invoiceId" not in attrs
    assert "REDACTED" not in str(attrs)


def test_missing_snapshot_quality_is_explained():
    assert finance_attributes(None, "electricity_costs")["quality"] == "not_published"


def test_unknown_finance_metric_rejected():
    with pytest.raises(ValueError):
        finance_reading(_snapshot(), "invented_capacity_tariff")
