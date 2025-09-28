
HA_NETWORK=ha-network

docker network create --driver bridge ${HA_NETWORK}

docker run -d  --network ${HA_NETWORK} --name ha --rm  -v ./hass_enki_component/custom_components:/config/custom_components -p 8123:8123 homeassistant/home-assistant

