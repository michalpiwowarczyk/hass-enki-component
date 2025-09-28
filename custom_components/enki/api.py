"""Enki API."""

import aiohttp
from dataclasses import dataclass
from typing import Any
import time

from .const import (
    LOGGER,
    ENKI_OIDC_URL,
    ENKI_URL,
    ENKI_HOME_API_KEY,
    ENKI_BFF_API_KEY,
    ENKI_NODE_API_KEY,
    ENKI_REFERENTIEL_API_KEY,
    ENKI_LIGHTS_API_KEY,
    ENKI_ROLLER_SHUTTER_API_KEY)

proxy = None

@dataclass
class Device:
    """API device."""
    home_id: str
    device_id: str
    node_id: str
    device_name: str

class API:
    """Class for Enki API."""

    def __init__(self, user: str, pwd: str) -> None:
        """Initialise."""
        self.user = user
        self.pwd = pwd

    @property
    def controller_name(self) -> str:
        """Return the name of the controller."""
        return self.user

    async def check_connected(self) -> bool:
        """Tell if token is still valid"""
        if not hasattr(self, '_access_token') or time.time()>self._tokenExpiresTime:
             await self.connect()
        return True

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
                        #LOGGER.warning("connect")
                        LOGGER.info("connect : " + str(response))
                        self._access_token = response["access_token"]
                        self._refresh_token = response["refresh_token"]
                        self._token_type = response["token_type"]
                        tokenExpiresTime = time.time() + response["expires_in"]*1000
                        self._tokenExpiresTime = tokenExpiresTime
                        return True
                    else:
                        raise APIAuthError("Error connecting to api. Invalid username or password.")
        except Exception as e:
            raise APIConnectionError("Error connecting to api : " + repr(e))

    async def get_homes(self):
        """Get list of homes."""
        await self.check_connected()
        homes = []
        async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-home-prod/v1/homes",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "X-Gateway-APIKey": ENKI_HOME_API_KEY},
             proxy=proxy,) as resp:

                if resp.status == 200:
                    response = await resp.json()
                    LOGGER.warning("get_homes")
                    LOGGER.info("get_homes : " + str(response))
                    for home in response["items"]:
                        homes.append(home["id"])
                    return homes
                else:
                    raise ValueError("bad credentials")

    def merge_properties(self, device, properties):
         for prop in properties:
            if prop != "id":
                device[prop] = properties[prop]

    def skip_property(self, properties, to_skip: str):
         props = []
         for prop in properties:
            if prop != to_skip:
                props[prop] = properties[prop]
         return props

    async def get_items_in_section_for_home(self, home_id) -> list[dict[str, Any]]:
            """Get sections in home."""
            await self.check_connected()
            async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-mobile-bff-prod/v1/dashboard/homes/{home_id}?hasGroups=true",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "X-Gateway-APIKey": ENKI_BFF_API_KEY},
             proxy=proxy,) as resp:
                devices = []
                if resp.status == 200:
                    response = await resp.json()
                    #LOGGER.warning("get_items_in_section_for_home")
                    LOGGER.info("get_items_in_section_for_home : " + str(response))
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
                            #LOGGER.warning("nodeId=" + device.get("nodeId"))
                            #LOGGER.warning("deviceId=" + device.get("deviceId"))
                            #LOGGER.warning("deviceName=" + device.get("deviceName"))
                            devices.append(device)

                            node_info = await self.get_node(home_id, device.get("nodeId"))
                            self.merge_properties(device, node_info)
                            
                            device_info = await self.get_device(device.get("deviceId"))
                            self.merge_properties(device, device_info)

                            await self.refresh_device(device)

                            #LOGGER.warning("device : " + repr(device))
                    return devices
                  
                else:
                    raise ValueError("bad credentials")

    async def refresh_device(self, device): 
        """Update device details"""
        #LOGGER.warning("Update device details, nodeId=" + device.get("nodeId") + ", deviceId=" + device.get("deviceId"))
        device_info = await self.get_device(device.get("deviceId"))
        self.merge_properties(device, device_info)
        if device["type"] == "lights" and device["isEnabled"]:
            # get lights details (on/off, brightness, temperature, etc)
            light_details = await self.get_light_details(device.get("homeId"), device.get("nodeId"))
            self.merge_properties(device, light_details)
        if device["type"] == "access_and_motorizations" and device["isEnabled"]:
            # get roller shutter details
            roller_shutter_details = await self.get_roller_shutter_details(device.get("homeId"), device.get("nodeId"))
            self.merge_properties(device, roller_shutter_details)
        return device

    async def get_node(self, home_id, node_id):
        """Get details on a node."""
        await self.check_connected()
        async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-node-agg-prod/v1/nodes/{node_id}",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "X-Gateway-APIKey": ENKI_NODE_API_KEY,
                      "homeId": f"{home_id}"},
             proxy=proxy,) as resp:

                if resp.status == 200:
                    response = await resp.json()
                    #LOGGER.warning("get_node " + node_id)
                    LOGGER.info("get_node : " + str(response))
                    return response

                else:
                    raise ValueError("bad credentials")

    async def get_device(self, id):
        """Get details on a device."""
        await self.check_connected()
        async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-referentiel-agg-prod/v1/devices/{id}?version=2.15.0",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "X-Gateway-APIKey": ENKI_REFERENTIEL_API_KEY},
             proxy=proxy,) as resp:

                if resp.status == 200:
                    response = await resp.json()
                    #LOGGER.warning("get_device " + id)
                    LOGGER.info("get_device : " + str(response))
                    return response

                else:
                    raise ValueError("bad credentials")

    async def get_light_details(self,home_id, node_id):
         """Get light state"""
         await self.check_connected()
         async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-lighting-prod/v1/lighting/{node_id}/check-light-state",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "homeId": home_id,
                      "X-Gateway-APIKey": ENKI_LIGHTS_API_KEY},
             proxy=proxy,) as resp:

                if resp.status == 200:
                    response = await resp.json()
                    #LOGGER.warning("get_light_details : " + str(response))
                    return response

                else:
                    raise ValueError("bad credentials")

    async def change_light_state(self, home_id, node_id, parameter, value):
        await self.check_connected()
        
        data = (await self.get_light_details(home_id, node_id))["lastReportedValue"]
        data[parameter] = value
        
        async with aiohttp.ClientSession() as session, session.request(
            method="POST",
            url=f"{ENKI_URL}/api-enki-lighting-prod/v1/lighting/{node_id}/change-light-state",
            headers={"Authorization": f"{self._token_type} {self._access_token}",
                    "homeId": home_id,
                    "X-Gateway-APIKey": ENKI_LIGHTS_API_KEY},
            proxy=proxy,
            json=data) as resp:

                if resp.status != 202:
                    response = await resp.json()
                    #LOGGER.warning(resp.status)
                    #LOGGER.warning(response)
                    raise ValueError("bad credentials")

    async def get_roller_shutter_details(self,home_id, node_id):
         """Get roller shutter state"""
         await self.check_connected()
         async with aiohttp.ClientSession() as session, session.request(
             method="GET",
             url=f"{ENKI_URL}/api-enki-rolling-prod/v1/shutter/{node_id}/check-roller-shutter-state",
             headers={"Authorization": f"{self._token_type} {self._access_token}",
                      "homeId": home_id,
                      "X-Gateway-APIKey": ENKI_ROLLER_SHUTTER_API_KEY},
             proxy=proxy,) as resp:

                if resp.status == 200:
                    response = await resp.json()
                    #LOGGER.warning("get_roller_shutter_details " + node_id)
                    LOGGER.info("get_roller_shutter_details : " + str(response))
                    return response

                else:
                    raise ValueError("bad credentials")

    async def change_roller_shutter_state(self, home_id, node_id, value):
        await self.check_connected()

        data = {
            "value": value
        }

        async with aiohttp.ClientSession() as session, session.request(
                method="POST",
                url=f"{ENKI_URL}/api-enki-rolling-prod/v1/shutter/{node_id}/change-shutter-position",
                headers={"Authorization": f"{self._token_type} {self._access_token}",
                         "homeId": home_id,
                         "X-Gateway-APIKey": ENKI_ROLLER_SHUTTER_API_KEY},
                proxy=proxy,
                json=data) as resp:
            if resp.status != 202:
                response = await resp.json()
                #LOGGER.warning("change_roller_shutter_state " + node_id)
                #LOGGER.warning(resp.status)
                #LOGGER.warning(response)
                raise ValueError("bad credentials")
            if resp.status == 202:
                LOGGER.warning(f"change_roller_shutter_state nodeId={node_id}, value={value}")

    async def get_devices(self) -> list[dict[str, Any]]:
        """Get devices on api."""
        #LOGGER.warning("Get homes in get devices")
        homes = await self.get_homes()
        devices = []
        for home in homes:
            devices.extend(await self.get_items_in_section_for_home(home))

        return devices

class APIAuthError(Exception):
    """Exception class for auth error."""

class APIConnectionError(Exception):
    """Exception class for connection error."""
