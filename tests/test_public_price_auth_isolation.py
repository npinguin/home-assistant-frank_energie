"""Regression tests for public-price authentication isolation.

Public MarketPrices must use an anonymous client even when a Frank Energie
account is configured; customerMarketPrices must keep the authenticated one.
"""
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch, sentinel

import pytest

from custom_components.frank_energie.coordinator import FrankEnergiePriceCoordinator


@pytest.fixture
def clients():
    hass = MagicMock()
    hass.config.country = "BE"
    entry = MagicMock()
    entry.data = {}
    entry.options = {"resolution": "PT15M"}
    entry.entry_id = "test-auth-isolation"

    authenticated = MagicMock()
    authenticated.is_authenticated = True
    authenticated.country_prices = AsyncMock()
    authenticated.prices = AsyncMock()
    authenticated.user_prices = AsyncMock(return_value=sentinel.customer_prices)

    with (
        patch(
            "custom_components.frank_energie.coordinator.async_get_clientsession",
            return_value=sentinel.ha_session,
        ),
        patch("custom_components.frank_energie.coordinator.FrankEnergie") as factory,
    ):
        public = factory.return_value
        public.is_authenticated = False
        public.country_prices = AsyncMock(return_value=sentinel.public_prices)
        public.prices = AsyncMock(return_value=sentinel.public_prices)
        coordinator = FrankEnergiePriceCoordinator(hass, entry, authenticated, MagicMock())
        yield coordinator, authenticated, public, factory


@pytest.mark.asyncio
async def test_belgian_public_prices_are_anonymous_even_when_logged_in(clients):
    coordinator, authenticated, public, factory = clients
    factory.assert_called_once_with(clientsession=sentinel.ha_session)
    assert coordinator.api is authenticated
    assert coordinator._public_api is public
    assert public.is_authenticated is False

    start, end = date(2026, 10, 21), date(2026, 10, 22)
    result = await coordinator._fetch_public_prices_for_range(start, end, "BE")

    assert result is sentinel.public_prices
    public.country_prices.assert_awaited_once_with("BE", start, end, "PT15M")
    authenticated.country_prices.assert_not_awaited()
    authenticated.prices.assert_not_awaited()


@pytest.mark.asyncio
async def test_other_countries_public_prices_remain_anonymous(clients):
    coordinator, authenticated, public, _ = clients
    start, end = date(2026, 10, 21), date(2026, 10, 22)
    result = await coordinator._fetch_public_prices_for_range(start, end, "NL")

    assert result is sentinel.public_prices
    public.prices.assert_awaited_once_with(start, resolution="PT15M")
    authenticated.prices.assert_not_awaited()


@pytest.mark.asyncio
async def test_customer_prices_still_use_authenticated_client(clients):
    coordinator, authenticated, public, _ = clients
    coordinator._site_reference = "test-site"
    coordinator._user_country = "BE"
    start, end = date(2026, 10, 21), date(2026, 10, 22)

    result = await coordinator._fetch_user_prices_for_range(start, end, "BE")

    assert result is sentinel.customer_prices
    authenticated.user_prices.assert_awaited_once_with("test-site", "BE", start, end)
    public.country_prices.assert_not_awaited()
    public.prices.assert_not_awaited()
