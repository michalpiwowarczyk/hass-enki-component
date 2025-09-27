"""Roller shutter setup for our Integration."""

from typing import Optional
from typing import Any

from homeassistant.components.cover import CoverEntity
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
            EnkiRollerShutter(coordinator, device, "state")
            for device in coordinator.data
            if device.get("type") == "access_and_motorizations"
        ]
    )

    # Create the covers.
    async_add_entities(covers)

class EnkiRollerShutter(EnkiBaseEntity, CoverEntity):

    def __init__(
        self, coordinator: EnkiCoordinator, device: dict[str, Any], parameter: str
    ) -> None:
        """Initialise entity."""
        super().__init__(coordinator, device, parameter)
        self._device = device

    @property
    def is_on(self) -> bool | None:
        """Return if the binary sensor is on."""
        # This needs to enumerate to true or false
        last_reported_values = self.coordinator.get_device_parameter(self.device_id, "lastReportedValue")
        return (
            last_reported_values["power"] == "ON"
        )

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        if "position" in kwargs:
            ha_value = kwargs["position"]
            value = int(ha_value)
            LOGGER.debug(f"setting position value to {ha_value} => {value}")
            await self.coordinator.api.change_roller_shutter_state(self._device["homeId"], self._device["nodeId"], "value", value)
            self.coordinator.update_data(self.device_id, "lastReportedValue", "current_position", value)

    @property
    def position(self) -> Optional[int]:
        """Return the current position."""
        last_reported_values = self.coordinator.get_device_parameter(self.device_id, "lastReportedValue")
        return last_reported_values
