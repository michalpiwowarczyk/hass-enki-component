"""Light setup for our Integration."""

from datetime import timedelta
#import logging
from typing import Any

#import voluptuous as vol

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MyConfigEntry
from .base import ExampleBaseEntity
#from .const import CONF_OFF_TIME, SET_OFF_TIMER_ENTITY_SERVICE_NAME
from .coordinator import ExampleCoordinator

#_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MyConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Binary Sensors."""
    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: ExampleCoordinator = config_entry.runtime_data.coordinator

    # ----------------------------------------------------------------------------
    # Here we are going to add some lights entities for the lights in our mock data.
    # We have an on/off light and a dimmable light in our mock data, so add each
    # specific class based on the light type.
    # ----------------------------------------------------------------------------
    lights = []

    # On/Off lights
    lights.extend(
        [
            ExampleOnOffLight(coordinator, device, "state")
            for device in coordinator.data
            if device.get("type") == "ON_OFF_LIGHT"
        ]
    )

    # Dimmable lights
    lights.extend(
        [
            ExampleDimmableLight(coordinator, device, "state")
            for device in coordinator.data
            if device.get("type") == "DIMMABLE_LIGHT"
        ]
    )

    lights.extend(
        [
            EnkiLight(coordinator, device, "state")
            for device in coordinator.data
            if device.get("type") == "lights"
        ]
    )

    # Create the lights.
    async_add_entities(lights)

class EnkiLight(ExampleBaseEntity, LightEntity):
    """Implementation of an light depending on its capabilities."""
    _attr_supported_color_modes = set()
    _attr_color_mode = None

    def __init__(
        self, coordinator: ExampleCoordinator, device: dict[str, Any], parameter: str
    ) -> None:
        """Initialise entity."""
        super().__init__(coordinator, device, parameter)
        if "switch_electrical_power" in  device["capabilities"]:
            self._attr_supported_color_modes.add(ColorMode.ONOFF)
            self._attr_color_mode = ColorMode.ONOFF
        
        if "change_color_temperature" in device["capabilities"]:
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)
            self._attr_color_mode = ColorMode.COLOR_TEMP

        if "change_brightness" in device["capabilities"]:
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
            self._attr_color_mode = ColorMode.BRIGHTNESS

class ExampleOnOffLight(ExampleBaseEntity, LightEntity):
    """Implementation of an on/off light.

    This inherits our ExampleBaseEntity to set common properties.
    See base.py for this class.

    https://developers.home-assistant.io/docs/core/entity/light/
    """

    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    @property
    def is_on(self) -> bool | None:
        """Return if the binary sensor is on."""
        # This needs to enumerate to true or false
        return (
            self.coordinator.get_device_parameter(self.device_id, self.parameter)
            == "ON"
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_data, self.device_id, self.parameter, "ON"
        )
        # ----------------------------------------------------------------------------
        # Use async_refresh on the DataUpdateCoordinator to perform immediate update.
        # Using self.async_update or self.coordinator.async_request_refresh may delay update due
        # to trying to batch requests.
        # ----------------------------------------------------------------------------
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_data, self.device_id, self.parameter, "OFF"
        )
        # ----------------------------------------------------------------------------
        # Use async_refresh on the DataUpdateCoordinator to perform immediate update.
        # Using self.async_update or self.coordinator.async_request_refresh may delay update due
        # to trying to batch requests.
        # ----------------------------------------------------------------------------
        await self.coordinator.async_refresh()

    async def async_set_off_timer(self, off_time: timedelta) -> None:
        """Handle the set off timer service call.

        Important here to have your service parameters included in your
        function as they are passed as named parameters.
        """
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_data,
            self.device_id,
            "off_timer",
            ":".join(str(off_time).split(":")[:2]),
        )
        # We have made a change to our device, so call a refresh to get updated data.
        # We use async_request_refresh here to batch the updates in case you select
        # multiple entities.
        await self.coordinator.async_request_refresh()


class ExampleDimmableLight(ExampleOnOffLight):
    """Implementation of a dimmable light."""

    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 0..255."""
        # Our light is in range 0..100, so convert
        return int(
            self.coordinator.get_device_parameter(self.device_id, "brightness")
            * (255 / 100)
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS] * (100 / 255))
            await self.hass.async_add_executor_job(
                self.coordinator.api.set_data, self.device_id, "brightness", brightness
            )
        else:
            await self.hass.async_add_executor_job(
                self.coordinator.api.set_data, self.device_id, self.parameter, "ON"
            )
        # ----------------------------------------------------------------------------
        # Use async_refresh on the DataUpdateCoordinator to perform immediate update.
        # Using self.async_update or self.coordinator.async_request_refresh may delay update due
        # to trying to batch requests and cause wierd UI behaviour.
        # ----------------------------------------------------------------------------
        await self.coordinator.async_refresh()
