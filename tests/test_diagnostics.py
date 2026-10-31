"""Tests for Frank Energie diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from types import SimpleNamespace
from uuid import UUID
from unittest.mock import MagicMock

import pytest

from custom_components.frank_energie.diagnostics import (
    _serialize,
    async_get_config_entry_diagnostics,
)


@dataclass
class MockDataclass:
    """Test dataclass."""

    name: str
    value: int


class MockEnum(Enum):
    """Test enum."""

    VALUE = "test"


class MockObject:
    """Test object."""

    def __init__(self) -> None:
        """Initialize test object."""
        self.public = "value"
        self._private = "hidden"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("test", "test"),
        (123, 123),
        (12.34, 12.34),
        (True, True),
    ],
)
def test_serialize_basic_types(
    value: object,
    expected: object,
) -> None:
    """Test serialization of basic types."""
    assert _serialize(value) == expected


def test_serialize_decimal() -> None:
    """Test Decimal serialization."""
    assert _serialize(Decimal("12.34")) == "12.34"


def test_serialize_datetime() -> None:
    """Test datetime serialization."""
    value = datetime(2026, 1, 1, 12, 0, 0)

    assert _serialize(value) == "2026-01-01T12:00:00"


def test_serialize_date() -> None:
    """Test date serialization."""
    value = date(2026, 1, 1)

    assert _serialize(value) == "2026-01-01"


def test_serialize_time() -> None:
    """Test time serialization."""
    value = time(12, 30, 45)

    assert _serialize(value) == "12:30:45"


def test_serialize_enum() -> None:
    """Test enum serialization."""
    assert _serialize(MockEnum.VALUE) == "test"


def test_serialize_uuid() -> None:
    """Test UUID serialization."""
    value = UUID("12345678-1234-5678-1234-567812345678")

    assert _serialize(value) == "12345678-1234-5678-1234-567812345678"


def test_serialize_bytes() -> None:
    """Test bytes serialization."""
    assert _serialize(b"\x01\x02") == "0102"


def test_serialize_tuple() -> None:
    """Test tuple serialization."""
    assert _serialize((1, "a")) == [1, "a"]


def test_serialize_set() -> None:
    """Test set serialization."""
    result = _serialize({"b", "a"})

    assert result == ["a", "b"]


def test_serialize_frozenset() -> None:
    """Test frozenset serialization."""
    result = _serialize(frozenset({"b", "a"}))

    assert result == ["a", "b"]


def test_serialize_dataclass() -> None:
    """Test dataclass serialization."""
    value = MockDataclass(
        name="test",
        value=123,
    )

    assert _serialize(value) == {
        "name": "test",
        "value": 123,
    }


def test_serialize_object() -> None:
    """Test generic object serialization."""
    assert _serialize(MockObject()) == {
        "public": "value",
    }


@pytest.mark.asyncio
async def test_diagnostics_redacts_sensitive_data() -> None:
    """Test diagnostics redact sensitive data."""

    coordinator = SimpleNamespace(
        last_update_success=True,
        update_interval=timedelta(minutes=15),
        site_reference="secret-site",
        country_code="NL",
        _user_country="NL",
        resolution="PT15M",
        api_resolution="PT15M",
        user_electricity_enabled=True,
        user_gas_enabled=True,
        last_fetch_today="today",
        last_fetch_tomorrow="tomorrow",
        cached_prices={},
        cached_prices_today={},
        cached_prices_tomorrow={},
        _resolution_change_pending=False,
        data={
            "email": "test@example.com",
            "ean": "871234567890123456",
            "safe": "value",
        },
    )

    runtime_data = SimpleNamespace(
        coordinator=coordinator,
        battery_session_coordinators=[],
    )

    entry = MagicMock()
    entry.entry_id = "123"
    entry.title = "Frank Energie"
    entry.options = {}
    entry.data = {
        "username": "user@example.com",
        "password": "secret",
        "access_token": "token",
        "site_reference": "site",
    }
    entry.runtime_data = runtime_data

    diagnostics = await async_get_config_entry_diagnostics(
        MagicMock(),
        entry,
    )

    assert diagnostics["entry"]["data"]["username"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["password"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["access_token"] == "**REDACTED**"
    assert diagnostics["entry"]["data"]["site_reference"] == "**REDACTED**"

    assert diagnostics["data"]["email"] == "**REDACTED**"
    assert diagnostics["data"]["ean"] == "**REDACTED**"

    assert diagnostics["data"]["safe"] == "value"


@pytest.mark.asyncio
async def test_diagnostics_coordinator_metadata() -> None:
    """Test coordinator metadata is included."""

    coordinator = SimpleNamespace(
        last_update_success=True,
        update_interval=timedelta(minutes=15),
        site_reference="site",
        country_code="NL",
        _user_country="NL",
        resolution="PT15M",
        api_resolution="PT15M",
        user_electricity_enabled=True,
        user_gas_enabled=False,
        last_fetch_today="today",
        last_fetch_tomorrow="tomorrow",
        cached_prices={"prices": []},
        cached_prices_today={"prices": []},
        cached_prices_tomorrow={"prices": []},
        _resolution_change_pending=True,
        data={},
    )

    runtime_data = SimpleNamespace(
        coordinator=coordinator,
        battery_session_coordinators=[object(), object()],
    )

    entry = MagicMock()
    entry.entry_id = "123"
    entry.title = "Frank Energie"
    entry.options = {}
    entry.data = {}
    entry.runtime_data = runtime_data

    diagnostics = await async_get_config_entry_diagnostics(
        MagicMock(),
        entry,
    )

    coordinator_data = diagnostics["coordinator"]

    assert coordinator_data["last_update_success"] is True
    assert coordinator_data["country_code"] == "NL"
    assert coordinator_data["resolution"] == "PT15M"
    assert coordinator_data["api_resolution"] == "PT15M"
    assert coordinator_data["user_electricity_enabled"] is True
    assert coordinator_data["user_gas_enabled"] is False
    assert coordinator_data["has_cached_prices"] is True
    assert coordinator_data["has_cached_today"] is True
    assert coordinator_data["has_cached_tomorrow"] is True
    assert coordinator_data["resolution_change_pending"] is True

    assert diagnostics["battery_session_coordinators"] == 2


@pytest.mark.asyncio
async def test_diagnostics_distinguish_coordinator_health_from_data_coverage() -> None:
    """Price success must not be mistaken for successful monthly accounting."""
    price = SimpleNamespace(
        last_update_success=True,
        update_interval=timedelta(minutes=60),
        data={
            "electricity": SimpleNamespace(prices=[], resolution_minutes=60),
            "gas": SimpleNamespace(prices=[], resolution_minutes=60),
        },
    )
    statistics = SimpleNamespace(
        last_update_success=False,
        update_interval=timedelta(hours=1),
        data={
            "month_summary": None,
            "invoices": None,
            "usage": None,
            "month_insights_current": None,
            "month_insights_previous": None,
        },
    )
    coordinator = SimpleNamespace(
        last_update_success=True,
        update_interval=timedelta(minutes=60),
        site_reference="private",
        country_code="BE",
        _user_country="BE",
        resolution="PT15M",
        api_resolution=None,
        user_electricity_enabled=False,
        user_gas_enabled=False,
        last_fetch_today=None,
        last_fetch_tomorrow=None,
        cached_prices=None,
        cached_prices_today=None,
        cached_prices_tomorrow=None,
        _resolution_change_pending=False,
        data=price.data,
    )
    runtime = SimpleNamespace(
        coordinator=coordinator,
        price_coordinator=price,
        statistics_coordinator=statistics,
        battery_session_coordinators={},
    )
    entry = MagicMock()
    entry.entry_id = "private-entry"
    entry.title = "Private address"
    entry.data = {"site_reference": "private"}
    entry.options = {"username": "private-email"}
    entry.runtime_data = runtime

    diagnostics = await async_get_config_entry_diagnostics(MagicMock(), entry)
    evidence = diagnostics["coordinator_evidence"]
    assert evidence["price"]["last_update_success"] is True
    assert evidence["statistics"]["last_update_success"] is False
    assert evidence["price_coverage"]["electricity"]["price_points"] == 0
    assert evidence["price_coverage"]["electricity"]["resolution_minutes"] == 60
    assert evidence["finance_coverage"]["month_summary"] is False
    assert evidence["finance_coverage"]["month_insights_previous"] is False
    assert evidence["finance_coverage"]["invoices"] is False
    assert "private" not in str(evidence)
