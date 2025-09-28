"""Roller shutter setup for our Integration."""

from typing import Optional
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from . import EnkiConfigEntry
from .base import EnkiBaseEntity
from .coordinator import EnkiCoordinator
from .const import LOGGER

STATE_NORMAL = "NORMAL"
STATE_INVERTED = "INVERTED"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EnkiConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Binary Sensors."""
    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: EnkiCoordinator = config_entry.runtime_data.coordinator

    # ----------------------------------------------------------------------------
    # Here we are going to add some lights entities for the lights in our mock data.
    # We have an on/off light and a dimmable light in our mock data, so add each
    # specific class based on the light type.
    # ----------------------------------------------------------------------------
    covers = []

    covers.extend(
        [
            EnkiCoverModeSensor(coordinator, device, "mode")
            for device in coordinator.data
            if device.get("type") == "access_and_motorizations"
        ]
    )
    covers.extend(
        [
            EnkiGatewaySensor(coordinator, device, "model", "modelNumber")
            for device in coordinator.data
            if device.get("type") == "gateways"
        ]
    )
    covers.extend(
        [
            EnkiGatewaySensor(coordinator, device, "version", "version")
            for device in coordinator.data
            if device.get("type") == "gateways"
        ]
    )

    # Create the covers.
    async_add_entities(covers)

class EnkiCoverModeSensor(EnkiBaseEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [
        STATE_NORMAL,
        STATE_INVERTED,
    ]
    _attr_translation_key = "shutterMode"

    def __init__(
        self, coordinator: EnkiCoordinator, device: dict[str, Any], parameter: str
    ) -> None:
        """Initialise entity."""
        super().__init__(coordinator, device, parameter)
        self._device = device
        self._attr_native_value = device.get("lastReportedValue")["shutterModeEnum"]

    def enki_update(self, key, value) -> None:
        if key == "mode":
            self._attr_native_value = value

    async def async_update(self) -> None:
        if False:
            LOGGER.info("update")

class EnkiGatewaySensor(EnkiBaseEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: EnkiCoordinator, device: dict[str, Any], parameter: str, device_attribute: str
    ) -> None:
        """Initialise entity."""
        super().__init__(coordinator, device, parameter)
        self._device = device
        self._attr_native_value = device.get(device_attribute)

    def enki_update(self, key, value) -> None:
        if key == "value":
            self._attr_native_value = value

    async def async_update(self) -> None:
        if False:
            LOGGER.info("update")