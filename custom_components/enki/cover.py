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
import asyncio

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
            EnkiCover(coordinator, device, "state")
            for device in coordinator.data
            if device.get("type") == "access_and_motorizations"
        ]
    )

    # Create the covers.
    async_add_entities(covers)

class EnkiCover(EnkiBaseEntity, CoverEntity):

    def __init__(
        self, coordinator: EnkiCoordinator, device: dict[str, Any], parameter: str
    ) -> None:
        """Initialise entity."""
        super().__init__(coordinator, device, parameter)
        self._device = device
        self._attr_current_cover_position = int(device.get("lastReportedValue")["shutterPosition"])
        self._attr_shutter_mode = device.get("lastReportedValue")["shutterModeEnum"]
        _attr_is_closed = int(device.get("lastReportedValue")["shutterPosition"]) == 0
        _attr_is_closing = False
        _attr_is_opening = False
        _attr_state: None = None

    @property
    def is_closed(self) -> bool | None:
        """Return if the binary sensor is on."""
        # This needs to enumerate to true or false
        last_reported_values = self.coordinator.get_device_parameter(self.device_id, "lastReportedValue")
        return int(last_reported_values["shutterPosition"]) == 0

    def enki_update(self, key, value) -> None:
        if key == "position":
            self._attr_current_cover_position = int(value)
            self.coordinator.update_data(self.device_id, "lastReportedValue", "shutterPosition", int(value))
        if key == "mode":
            self._attr_shutter_mode = value

    def set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        raise NotImplementedError

    # async def update(self) -> None:
    #     # LOGGER.warning(f"user "+ self.coordinator.api.controller_name)
    #     for i in range (0, 15):
    #         await self.coordinator.api.check_connected()
    #         roller_shutter_details = await self.coordinator.api.get_roller_shutter_details(self._device["homeId"], self._device["nodeId"])
    #         self._attr_current_cover_position = int(roller_shutter_details["lastReportedValue"]["shutterPosition"])
    #         await asyncio.sleep(2)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        if "position" in kwargs:
            ha_value = kwargs["position"]
            value = int(ha_value)
            LOGGER.warning(f"setting position value to {ha_value} => {value}")
            await self.coordinator.api.change_roller_shutter_state(self._device["homeId"], self._device["nodeId"], value)
            # await self.update()

    def close_cover(self, **kwargs: Any) -> None:
        async def run():
            LOGGER.warning(f"closing cover")
            await self.change_shutter_state(0)
        asyncio.run(run())

    def open_cover(self, **kwargs: Any) -> None:
        async def run():
            LOGGER.warning(f"opening cover")
            await self.change_shutter_state(100)
        asyncio.run(run())

    async def change_shutter_state(self, value: int) -> None:
        await self.coordinator.api.change_roller_shutter_state(self._device["homeId"], self._device["nodeId"], value)
        # await self.update()

    @property
    def position(self) -> Optional[int]:
        """Return the current position."""
        last_reported_values = self.coordinator.get_device_parameter(self.device_id, "lastReportedValue")
        value = last_reported_values["shutterPosition"]
        LOGGER.warning(f"current position " + value)
        return int(value)

    @property
    def shutter_mode(self) -> Optional[str]:
        last_reported_values = self.coordinator.get_device_parameter(self.device_id, "lastReportedValue")
        value = last_reported_values["shutterModeEnum"]
        LOGGER.warning(f"current mode " + value)
        return value
