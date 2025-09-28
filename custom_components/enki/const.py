"""Constants for Enki integration."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

# This is the internal name of the integration, it should also match the directory
# name for the integration.
DOMAIN = "enki"
NAME = "Enki"

CONF_POOL_INTERVAL = "pool_interval_second"

ENKI_OIDC_URL = "https://keycloak-prod.iot.leroymerlin.fr/realms/enki/protocol/openid-connect/token"
ENKI_URL = "https://enki.api.devportal.adeo.cloud"
ENKI_HOME_API_KEY = "FULsxyI3x1f7MtLVOsP6V1DeAPmBQJCB"
ENKI_BFF_API_KEY = "Bco7qBHRHOQiSVcEHdgS0rijpebMBwkB"
ENKI_NODE_API_KEY = "UBb0Kv6xXpG6bOvD8VZ9A63uxqQ4G1A3"
ENKI_REFERENTIEL_API_KEY = "3uk9rlaIUgBsz1tEPV7GQMhhGfRwPFJY"
ENKI_LIGHTS_API_KEY = "3OVsNulRsUXfr7Hze54OHx8l6qDu2UcE"
ENKI_ROLLER_SHUTTER_API_KEY = "QegWuQR3zSKLlJZ2OITv94vjtSaaPkDp"