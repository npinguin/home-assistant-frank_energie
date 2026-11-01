"""HA diagnostic sensor for each service's live polling interval.

The state is the coordinator's current interval in minutes, not a promise
that Frank's API will publish data at that frequency. Attributes distinguish
observed GraphQL requests from an estimated next polling time.
"""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import API_CONF_URL, COMPONENT_TITLE, DOMAIN, SERVICE_NAME_PRICES, VERSION
from .helpers import device_translation_key
from .service_refresh import (
    RefreshService,
    service_refresh_attributes,
    service_refresh_interval_minutes,
)


class FrankEnergieRefreshIntervalSensor(CoordinatorEntity, SensorEntity):
    """Expose actual coordinator polling cadence on a service device."""

    _attr_has_entity_name = True
    _attr_name = "Refresh interval"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer-refresh"
    _attr_native_unit_of_measurement = "min"
    _attr_should_poll = False

    def __init__(
        self, service: RefreshService, entry: ConfigEntry, trace: object | None
    ) -> None:
        """Attach to the existing coordinator without any additional API calls."""
        super().__init__(service.coordinator)
        self._service = service
        self._trace = trace
        self._attr_unique_id = f"{entry.entry_id}_refresh_interval_{service.key}"
        identifier = (
            entry.entry_id
            if service.device_name == SERVICE_NAME_PRICES
            else f"{entry.entry_id}_{service.device_name}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=f"{COMPONENT_TITLE} - {service.device_name}",
            translation_key=device_translation_key(service.device_name),
            manufacturer=COMPONENT_TITLE,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=API_CONF_URL,
            sw_version=VERSION,
        )

    @property
    def native_value(self) -> float | None:
        """Live interval, including dynamic price polling."""
        return service_refresh_interval_minutes(self._service)

    @property
    def available(self) -> bool:
        """Keep scheduling information visible during provider outages."""
        return self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        """Observed request times, estimate and coordinator health."""
        return service_refresh_attributes(self._service, self._trace)
