"""API Placeholder.

You should create your api seperately and have it hosted on PYPI.  This is included here for the sole purpose
of making this example code executable.
"""
import aiohttp
from dataclasses import dataclass
from enum import StrEnum
from random import choice, randrange
from typing import Any

from .const import (
    LOGGER,
    ENKI_OIDC_URL,
    ENKI_URL,
    ENKI_HOME_API_KEY,
    ENKI_BFF_API_KEY,
    ENKI_NODE_API_KEY,
    ENKI_REFERENTIEL_API_KEY,
    ENKI_USER_API_KEY)

proxy = "http://proxy.rd.francetelecom.fr:8080/"
#proxy = None

class DeviceType(StrEnum):
    """Device types."""

    TEMP_SENSOR = "temp_sensor"
    DOOR_SENSOR = "door_sensor"
    OTHER = "other"

DEVICES = [
    {"id": 1, "type": DeviceType.TEMP_SENSOR},
    {"id": 2, "type": DeviceType.TEMP_SENSOR},
    {"id": 3, "type": DeviceType.TEMP_SENSOR},
    {"id": 4, "type": DeviceType.TEMP_SENSOR},
    {"id": 1, "type": DeviceType.DOOR_SENSOR},
    {"id": 2, "type": DeviceType.DOOR_SENSOR},
    {"id": 3, "type": DeviceType.DOOR_SENSOR},
    {"id": 4, "type": DeviceType.DOOR_SENSOR},
]


@dataclass
class Device:
    """API device."""
    home_id: str
    device_id: str
    node_id: str
    device_name: str
    
    #device_unique_id: str
    #device_type: DeviceType
    #name: str
    #state: int | bool

class API:
    """Class for example API."""

    def __init__(self, user: str, pwd: str) -> None:
        """Initialise."""
        self.user = user
        self.pwd = pwd
        self.connected: bool = False

    @property
    def controller_name(self) -> str:
        """Return the name of the controller."""
        return self.user

    async def connect(self) -> bool:
        """Connect to the Enki API."""
        try:
            async with aiohttp.ClientSession() as session, session.request(
                method="POST",
                url=ENKI_OIDC_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"grant_type":"password",
                    "client_id": "enki-front",
                    "username": self.user,
                    "password": self.pwd},
                proxy=proxy,) as resp:

                    if resp.status == 200:
                        response = await resp.json()
                        LOGGER.debug("connect : " + str(response))
                        self._access_token = response["access_token"]
                        self._refresh_token = response["refresh_token"]
                        self._token_type = response["token_type"]
                        self.connected = True
                        return True
                    else:
                        raise APIAuthError("Error connecting to api. Invalid username or password.")
        except Exception as e:
            raise APIConnectionError("Error connecting to api : " + repr(e))

# *******************************************************
    async def get_homes(self):
        """Get list of homes."""
        homes = []
        async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-home-prod/v1/homes",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "X-Gateway-APIKey": ENKI_HOME_API_KEY},
             proxy=proxy,) as resp:

                if resp.status == 200:
                    response = await resp.json()
                    LOGGER.debug("get_homes : " + str(response))
                    for home in response["items"]:
                        homes.append(home["id"])
                    return homes
                else:
                    raise ValueError("bad credentials")

    async def get_home(self, home_id):
        """Get details on home."""
        async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-home-prod/v1/homes/{home_id}",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "X-Gateway-APIKey": ENKI_HOME_API_KEY},
             proxy=proxy,) as resp:

              if resp.status == 200:
                  response = await resp.json()
                  LOGGER.debug("get_home : " + str(response))
              else:
                raise ValueError("bad credentials")

    async def get_items_in_section_for_home(self, home_id) -> list[dict[str, Any]]:
            """Get sections in home."""
            async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-mobile-bff-prod/v1/dashboard/homes/{home_id}?hasGroups=true",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "X-Gateway-APIKey": ENKI_BFF_API_KEY},
             proxy=proxy,) as resp:
                devices = []
                if resp.status == 200:
                    response = await resp.json()
                    LOGGER.debug("get_items_in_section_for_home : " + str(response))
                    for section in response["sections"]:
                        for item in section["items"]:
                            device = {
                                "homeId": home_id,
                                "deviceId": item["metadata"]["deviceId"],
                                "nodeId": item["metadata"]["nodeId"],
                                "deviceName": item["title"]["label"],
                                "state": item["state"],
                                "isEnabled": item["isEnabled"]
                            }
                            devices.append(device)

                            node_info = await self.get_node(home_id, device.get("nodeId"))
                            for info in node_info:
                                if info != "id":
                                    device[info] = node_info[info]
                            device_info = await self.get_device(device.get("deviceId"))
                            for info in device_info:
                                if info != "id":
                                    device[info] = device_info[info]
                            LOGGER.debug("device : " + repr(device))
                    return devices
                  
                else:
                    raise ValueError("bad credentials")

    async def get_node(self, home_id, node_id):
        """Get details on a node."""
        async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-node-agg-prod/v1/nodes/{node_id}",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "X-Gateway-APIKey": ENKI_NODE_API_KEY,
                      "homeId": f"{home_id}"},
             proxy=proxy,) as resp:

                if resp.status == 200:
                    response = await resp.json()
                    LOGGER.debug("get_node : " + str(response))
                    #print("\t\t" + response["icon"] + " " + response["factoryId"] + " " + response["modelNumber"])
                    return response

                else:
                    raise ValueError("bad credentials")

    async def get_device(self, id):
        """Get details on a device."""
        async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-referentiel-agg-prod/v1/devices/{id}?version=2.15.0",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "X-Gateway-APIKey": ENKI_REFERENTIEL_API_KEY},
             proxy=proxy,) as resp:

                if resp.status == 200:
                    response = await resp.json()
                    LOGGER.debug("get_device : " + str(response))
                    return response

                else:
                    raise ValueError("bad credentials")

    async def get_current_user(self):
         """Get details on the current user."""
         async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-user-prod/v1/users/current",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "X-Gateway-APIKey": ENKI_USER_API_KEY},
             proxy=proxy,) as resp:

                if resp.status == 200:
                    response = await resp.json()
                    LOGGER.debug(response)
                else:
                    raise ValueError("bad credentials")

# *******************************************************

    def disconnect(self) -> bool:
        """Disconnect from api."""
        self.connected = False
        return True

    async def get_devices(self) -> list[dict[str, Any]]:
        """Get devices on api."""
        homes = await self.get_homes()
        devices = []
        for home in homes:
            devices.extend(await self.get_items_in_section_for_home(home))

        return devices

class APIAuthError(Exception):
    """Exception class for auth error."""

class APIConnectionError(Exception):
    """Exception class for connection error."""
