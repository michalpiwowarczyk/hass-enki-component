docker run --network host --name ha --rm  -v $HOME/hass-enki-component/custom_components/:/config/custom_components/ -p 8123:8123 homeassistant/home-assistant
