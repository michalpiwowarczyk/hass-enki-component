"""Roller shutter setup for our Integration."""

from typing import Any

from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import EnkiConfigEntry
from .base import EnkiBaseEntity
from .coordinator import EnkiCoordinator
from .const import LOGGER

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
            EnkiCoverMode(coordinator, device, "mode-old")
            for device in coordinator.data
            if device.get("type") == "access_and_motorizations"
        ]
    )

    async_add_entities(covers)

class EnkiCoverMode(EnkiBaseEntity, TextEntity):

    def __init__(
        self, coordinator: EnkiCoordinator, device: dict[str, Any], parameter: str
    ) -> None:
        """Initialise entity."""
        super().__init__(coordinator, device, parameter)
        self._device = device
        self._attr_native_value = device.get("lastReportedValue")["shutterModeEnum"]
        _attr_state: None = None

    def set_value(self, value: str) -> None:
        LOGGER.info("ignored")

    def enki_update(self, key, value) -> None:
        if key == "mode":
            self._attr_native_value = value
