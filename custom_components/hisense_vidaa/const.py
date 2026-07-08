"""Constants for the Hisense VIDAA integration."""

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "hisense_vidaa"

CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_MAC: Final = "mac"
CONF_NAME: Final = "name"
CONF_DEVICE_ID: Final = "device_id"
CONF_MODEL: Final = "model"
CONF_SW_VERSION: Final = "sw_version"

DEFAULT_PORT: Final = 36669
DEFAULT_NAME: Final = "Hisense TV"
TOKEN_FILE: Final = ".hisense_vidaa_tokens.json"

TIMEOUT_CONNECT: Final = 10
TIMEOUT_COMMAND: Final = 5
TIMEOUT_VOLUME: Final = 2

SCAN_INTERVAL: Final = 30
VOLUME_REFRESH_DELAY: Final = 0.3

SERVICE_SEND_KEY: Final = "send_key"
SERVICE_LAUNCH_APP: Final = "launch_app"

ATTR_KEY: Final = "key"
ATTR_APP: Final = "app"

STATE_FAKE_SLEEP: Final = "fake_sleep_0"

PLATFORMS: Final = [Platform.MEDIA_PLAYER, Platform.REMOTE]

MANUFACTURER: Final = "Hisense"
