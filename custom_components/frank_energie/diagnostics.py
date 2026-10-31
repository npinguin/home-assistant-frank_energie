"""Diagnostics support for the Frank Energie integration."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from uuid import UUID

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_PASSWORD,
    CONF_TOKEN,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant

from . import FrankEnergieEntryData

TO_REDACT: set[str] = {
    CONF_ACCESS_TOKEN,
    CONF_TOKEN,
    CONF_USERNAME,
    CONF_PASSWORD,
    "authToken",
    "refreshToken",
    "access_token",
    "refresh_token",
    "password",
    "username",
    "email",
    "phone",
    "address",
    "customer_id",
    "customerId",
    "account_id",
    "accountId",
    "title",
    "contract_id",
    "contractId",
    "site_reference",
    "siteReference",
    "reference",
    "TotalAmount",
    "Total amount",
    "Total_amount",
    "total_costs_previous_year",
    "total_costs_this_year",
    "site_id",
    "siteId",
    "_id",
    "connection_id",
    "connectionId",
    "bankAccountNumber",
    "EAN",
    "cluster",
    "firstName",
    "lastName",
    "emailAddress",
    "phoneNumber",
    "mobileNumber",
    "ean",
    "electricity_ean",
    "gas_ean",
    "serial_number",
    "serialNumber",
    "battery_id",
    "batteryId",
    "charger_id",
    "chargerId",
    "vehicle_id",
    "vehicleId",
    "device_id",
    "deviceId",
    "installation_id",
    "installationId",
}


def _serialize(value: object) -> object:
    """Convert objects into diagnostics-safe structures."""
    if value is None:
        return None

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, bytes):
        return value.hex()

    if isinstance(value, (set, frozenset)):
        return [_serialize(item) for item in sorted(value, key=str)]

    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _serialize(getattr(value, field.name))
            for field in fields(value)
        }

    if isinstance(value, dict):
        return {str(key): _serialize(val) for key, val in value.items()}

    if isinstance(value, list):
        return [_serialize(item) for item in value]

    if isinstance(value, tuple):
        return [_serialize(item) for item in value]

    if hasattr(value, "__dict__"):
        return {
            key: _serialize(val)
            for key, val in vars(value).items()
            if not key.startswith("_")
        }

    return value



def _bounded_coordinator_evidence(coordinator: object | None) -> dict[str, object]:
    """Expose coordinator liveness and coverage, never its customer payload."""
    if coordinator is None:
        return {"configured": False}
    data = getattr(coordinator, "data", None)
    return {
        "configured": True,
        "last_update_success": getattr(coordinator, "last_update_success", None),
        "update_interval": str(getattr(coordinator, "update_interval", None)),
        "has_data": bool(data),
    }


def _safe_price_coverage(data: object) -> dict[str, object]:
    """Report empty price streams without serializing values or account data."""
    if not isinstance(data, dict):
        return {}
    coverage: dict[str, object] = {}
    for segment in ("electricity", "gas"):
        source = data.get(segment)
        if source is None:
            coverage[segment] = {"available": False}
            continue
        prices = getattr(source, "prices", None)
        coverage[segment] = {
            "available": True,
            "price_points": len(prices) if isinstance(prices, (list, tuple)) else None,
            "resolution_minutes": getattr(source, "resolution_minutes", None),
        }
    return coverage


def _safe_finance_coverage(data: object) -> dict[str, object]:
    """Report separate finance freshness without publishing private amounts."""
    if not isinstance(data, dict):
        return {}
    keys = (
        "month_summary",
        "invoices",
        "usage",
        "month_insights_current",
        "month_insights_previous",
    )
    result: dict[str, object] = {}
    for key in keys:
        snapshot = data.get(key)
        result[key] = snapshot is not None
    return result


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, object]:
    """Return diagnostics for a config entry."""

    runtime_data: FrankEnergieEntryData = entry.runtime_data
    coordinator = runtime_data.coordinator

    diagnostics: dict[str, object] = {
        "entry": {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "options": dict(entry.options),
            "data": dict(entry.data),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
            "site_reference": coordinator.site_reference,
            "country_code": coordinator.country_code,
            "user_country": getattr(coordinator, "_user_country", None),
            "resolution": coordinator.resolution,
            "api_resolution": coordinator.api_resolution,
            "user_electricity_enabled": coordinator.user_electricity_enabled,
            "user_gas_enabled": coordinator.user_gas_enabled,
            "last_fetch_today": coordinator.last_fetch_today,
            "last_fetch_tomorrow": coordinator.last_fetch_tomorrow,
            "has_cached_prices": coordinator.cached_prices is not None,
            "has_cached_today": coordinator.cached_prices_today is not None,
            "has_cached_tomorrow": coordinator.cached_prices_tomorrow is not None,
            "resolution_change_pending": getattr(
                coordinator,
                "_resolution_change_pending",
                False,
            ),
        },
        "data": _serialize(coordinator.data),
        "cached_prices": _serialize(coordinator.cached_prices),
        "battery_session_coordinators": len(
            runtime_data.battery_session_coordinators,
        ),
        # Explicit cross-coordinator evidence: a healthy price coordinator
        # cannot be used to infer invoice, metering or monthly-finance health.
        "coordinator_evidence": {
            "price": _bounded_coordinator_evidence(
                getattr(runtime_data, "price_coordinator", None)
            ),
            "settings": _bounded_coordinator_evidence(
                getattr(runtime_data, "settings_coordinator", None)
            ),
            "statistics": _bounded_coordinator_evidence(
                getattr(runtime_data, "statistics_coordinator", None)
            ),
            "price_coverage": _safe_price_coverage(coordinator.data),
            "finance_coverage": _safe_finance_coverage(
                getattr(getattr(runtime_data, "statistics_coordinator", None), "data", None)
            ),
        },
    }

    return async_redact_data(diagnostics, TO_REDACT)
