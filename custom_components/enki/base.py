"""Base entity which all other entity platform classes can inherit.

As all entity types have a common set of properties, you can
create a base entity like this and inherit it in all your entity platforms.

This just makes your code more efficient and is totally optional.

See each entity platform (ie sensor.py, switch.py) for how this is inheritted
and what additional properties and methods you need to add for each entity type.

"""

from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER
from .coordinator import EnkiCoordinator


class EnkiBaseEntity(CoordinatorEntity):
    """Base Entity Class.

    This inherits a CoordinatorEntity class to register your entites to be updated
    by your DataUpdateCoordinator when async_update_data is called, either on the scheduled
    interval or by forcing an update.
    """

    coordinator: EnkiCoordinator

    # ----------------------------------------------------------------------------
    # Using attr_has_entity_name = True causes HA to name your entities with the
    # device name and entity name.  Ie if your name property of your entity is
    # Voltage and this entity belongs to a device, Lounge Socket, this will name
    # your entity to be sensor.lounge_socket_voltage
    #
    # It is highly recommended (by me) to use this to give a good name structure
    # to your entities.  However, totally optional.
    # ----------------------------------------------------------------------------
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: EnkiCoordinator, device: dict[str, Any], parameter: str
    ) -> None:
        """Initialise entity."""
        super().__init__(coordinator)
        self.device = device
        self.device_id = device["nodeId"]
        #self.parameter = self.coordinator.get_device_parameter(self.device_id, "deviceName") + "-" + parameter
        self.parameter = parameter
#        self.entity_id = self.device_id + "-" + self.parameter

    def enki_update(self, key, value) -> None:
        raise NotImplementedError

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.device["isEnabled"] & (self.device["state"] != "DEACTIVATED")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        # This method is called by your DataUpdateCoordinator when a successful update runs.
        self.device = self.coordinator.get_device(self.device_id)
        LOGGER.warning(
            "Updating device: %s, %s",
            self.device_id,
            self.coordinator.get_device_parameter(self.device_id, "deviceName"),
        )
        try:
            value = self.device.get("lastReportedValue")["shutterPosition"]
            if value is not None:
                self.enki_update("position", value)
            value = self.device.get("lastReportedValue")["shutterModeEnum"]
            if value is not None:
                self.enki_update("mode", value)
        except Exception:
            pass

        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""

        # ----------------------------------------------------------------------------
        # Identifiers are what group entities into the same device.
        # If your device is created elsewhere, you can just specify the indentifiers
        # parameter to link an entity to a device.
        # If your device connects via another device, add via_device parameter with
        # the indentifiers of that device.
        #
        # Device identifiers should be unique, so use your integration name (DOMAIN)
        # and a device uuid, mac address or some other unique attribute.
        # ----------------------------------------------------------------------------
        return DeviceInfo(
            name=self.coordinator.get_device_parameter(self.device_id, "deviceName") + "-" + self.parameter,
            manufacturer=self.coordinator.get_device_parameter(self.device_id, "manufacturerId"),
            model=str(
                self.coordinator.get_device_parameter(self.device_id, "modelNumber")
            )
            .replace("_", " ")
            .title(),
            sw_version=self.coordinator.get_device_parameter(
                self.device_id, "version"
            ),
            identifiers={
                (
                    DOMAIN,
                    self.coordinator.get_device_parameter(self.device_id, "nodeId")
                )
            },
        )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.parameter.replace("_", " ").title()

    @property
    def unique_id(self) -> str:
        """Return unique id."""

        # ----------------------------------------------------------------------------
        # All entities must have a unique id across your whole Home Assistant server -
        # and that also goes for anyone using your integration who may have many other
        # integrations loaded.
        #
        # Think carefully what you want this to be as changing it later will cause HA
        # to create new entities.
        #
        # It is recommended to have your integration name (DOMAIN), some unique id
        # from your device such as a UUID, MAC address etc (not IP address) and then
        # something unique to your entity (like name - as this would be unique on a
        # device)
        #
        # If in your situation you have some hub that connects to devices which then
        # you want to create multiple sensors for each device, you would do something
        # like.
        #
        # f"{DOMAIN}-{HUB_MAC_ADDRESS}-{DEVICE_UID}-{ENTITY_NAME}""
        #
        # This is even more important if your integration supports multiple instances.
        # ----------------------------------------------------------------------------
        uid = f"unique_id={DOMAIN}-{self.device_id}-{self.parameter}"
        #return f"{DOMAIN}-{self.coordinator.get_device_parameter(self.device_id, "deviceId")}-{self.parameter}"
        LOGGER.warning(uid)
        #return f"{DOMAIN}-{self.coordinator.get_device_parameter(self.device_id, "deviceId")}"
        return uid
