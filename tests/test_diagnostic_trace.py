"""Actual Frank Energie GraphQL request observability without customer data."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from custom_components.frank_energie.diagnostic_trace import (
    DiagnosticTrace,
    _response_metadata,
    attach_graphql_trace,
)


def test_month_insights_raw_null_zero_distinction_without_finance_values() -> None:
    """Source null-vs-zero evidence survives before upstream parser coercion."""
    response = {
        "data": {
            "monthInsights": {
                "expectedCosts": None,
                "expectedCostsGas": 0,
                "expectedCostsElectricity": 481516.234,
                "gasDifference": {"actualUsage": None, "actualCosts": 0},
                "electricityDifference": {"actualUsage": 9.8},
                "lastMeterReadingDate": None,
            }
        }
    }
    result = _response_metadata(response)
    states = result["month_insights_source_states"]
    assert states["expectedCosts"] == "null"
    assert states["expectedCostsGas"] == "zero"
    assert states["expectedCostsElectricity"] == "positive"
    assert states["expectedCostsFeedIn"] == "missing"
    assert states["gasDifference.actualUsage"] == "null"
    assert states["gasDifference.actualCosts"] == "zero"
    assert states["electricityDifference.expectedUsage"] == "missing"
    assert states["lastMeterReadingDate"] == "null"
    assert "481516" not in str(result)
    assert "9.8" not in str(result)


def test_response_metadata_distinguishes_null_empty_and_present_price_arrays() -> None:
    """Observe raw GraphQL data before the provider parser can discard fields."""
    response = {
        "data": {
            "customerMarketPrices": {
                "electricityPrices": [{"allInPrice": 123456789, "id": "private"}],
                "gasPrices": [],
            },
            "monthSummary": None,
        },
        "errors": [{"message": "private-error-id-1234"}],
    }
    result = _response_metadata(response)
    assert result["data_present"] is True
    assert result["graphql_error_count"] == 1
    assert result["response_roots"]["monthSummary"] == "null"
    assert result["response_roots"]["customerMarketPrices"] == "present"
    assert result["response_electricity_slots"] == 1
    assert result["response_gas_slots"] == 0
    assert "123456789" not in str(result)
    assert "private-error-id-1234" not in str(result)


@pytest.mark.asyncio
async def test_observer_records_real_query_and_never_stores_payload() -> None:
    """Single GraphQL call, original result identity, no private variables."""
    calls = []
    response = {
        "data": {
            "marketPrices": {
                "electricityPrices": [{"marketPrice": 876543210}],
                "gasPrices": [],
            }
        }
    }

    async def original_query(query, extra_headers=None):
        calls.append((query, extra_headers))
        return response

    client = SimpleNamespace(_query=original_query)
    trace = DiagnosticTrace()
    attach_graphql_trace(client, trace, "graphql_public")
    attach_graphql_trace(client, trace, "graphql_public")  # idempotent

    query = SimpleNamespace(
        operation_name="MarketPrices",
        variables={"date": "2026-10-31", "siteReference": "sensitive-site"},
    )
    result = await client._query(
        query, extra_headers={"Authorization": "private-token"}
    )
    assert result is response
    assert len(calls) == 1

    snapshot = trace.snapshot()
    events = snapshot["events"]
    assert len(events) == 1
    assert events[0]["operation"] == "MarketPrices"
    assert events[0]["source"] == "graphql_public"
    assert events[0]["period"] == "2026-10-31"
    assert events[0]["outcome"] == "ok"
    assert events[0]["response_electricity_slots"] == 1
    assert events[0]["response_gas_slots"] == 0
    assert isinstance(events[0]["duration_ms"], int)
    assert events[0]["duration_ms"] >= 0
    for sensitive in ("sensitive-site", "private-token", "876543210"):
        assert sensitive not in str(snapshot)


@pytest.mark.asyncio
async def test_observer_captures_graphql_errors_and_reraises_network_failure() -> None:
    """Preserve vendor exception semantics, record only error type and counts."""
    trace = DiagnosticTrace()

    async def graphql_errors(query, extra_headers=None):
        return {"data": {"monthSummary": None}, "errors": [{"message": "private"}]}

    client = SimpleNamespace(_query=graphql_errors)
    attach_graphql_trace(client, trace, "graphql_account")
    query = SimpleNamespace(
        operation_name="MonthSummary", variables={"siteReference": "private"}
    )
    await client._query(query)
    assert trace.snapshot()["events"][0]["outcome"] == "graphql_errors"

    async def broken(query, extra_headers=None):
        raise RuntimeError("token=private-token account=secret")

    broken_client = SimpleNamespace(_query=broken)
    attach_graphql_trace(broken_client, trace, "graphql_account")
    with pytest.raises(RuntimeError, match="private-token"):
        await broken_client._query(query)
    event = trace.snapshot()["events"][-1]
    assert event["outcome"] == "exception"
    assert event["error_class"] == "RuntimeError"
    assert "private-token" not in str(trace.snapshot())


def test_price_observer_never_breaks_incomplete_provider_return_objects() -> None:
    """Telemetry must accept partial, unexpected, or sentinel-like API values."""
    from unittest.mock import sentinel

    from custom_components.frank_energie.coordinator import _price_counts

    assert _price_counts(None) == (0, 0)
    assert _price_counts(sentinel.unparsed_api_response) == (0, 0)
    assert _price_counts(SimpleNamespace(electricity=None, gas=None)) == (0, 0)
    assert _price_counts(
        SimpleNamespace(
            electricity=SimpleNamespace(all=[object(), object()]),
            gas=SimpleNamespace(all=[]),
        )
    ) == (2, 0)


def test_graphql_trace_stays_bounded_and_rejects_untrusted_operation_names() -> None:
    """Recent history is capped; operation metadata cannot be arbitrary text."""
    trace = DiagnosticTrace()
    for _ in range(160):
        trace.record(
            "graphql_account",
            "ok",
            operation="MarketPrices",
            response={"data": {"marketPrices": {}}},
        )
    events = trace.snapshot()["events"]
    assert len(events) == 96
    trace.record(
        "graphql_account",
        "ok",
        operation="private-id/secret:123",
        period="private-customer",
    )
    event = trace.snapshot()["events"][-1]
    assert event["operation"] == "unknown"
    assert "period" not in event
    assert "private-id/secret:123" not in str(trace.snapshot())
