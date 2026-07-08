"""The Hisense VIDAA integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from vidaa.keys import ALL_KEYS

from .client import HisenseVidaaClient
from .const import (
    ATTR_APP,
    ATTR_KEY,
    CONF_HOST,
    CONF_MAC,
    CONF_PORT,
    DEFAULT_PORT,
    DOMAIN,
    PLATFORMS,
    SERVICE_LAUNCH_APP,
    SERVICE_SEND_KEY,
    TOKEN_FILE,
)
from .coordinator import HisenseVidaaCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class HisenseVidaaRuntimeData:
    """Runtime data stored on the config entry."""

    coordinator: HisenseVidaaCoordinator
    client: HisenseVidaaClient


HisenseVidaaConfigEntry = ConfigEntry[HisenseVidaaRuntimeData]
CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration."""
    await _async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: HisenseVidaaConfigEntry) -> bool:
    """Set up Hisense VIDAA from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    mac = entry.data.get(CONF_MAC)
    token_path = Path(hass.config.config_dir) / TOKEN_FILE

    client = HisenseVidaaClient(
        host=host,
        port=port,
        mac_address=mac,
        token_path=token_path,
    )

    try:
        if not await client.connect(timeout=10):
            raise ConfigEntryNotReady("Failed to connect to TV")
    except ConfigEntryNotReady:
        raise
    except Exception as err:  # noqa: BLE001
        raise ConfigEntryNotReady("Error connecting to TV") from err

    coordinator = HisenseVidaaCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = HisenseVidaaRuntimeData(
        coordinator=coordinator,
        client=client,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HisenseVidaaConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and entry.runtime_data.client:
        await entry.runtime_data.client.disconnect()
    return unload_ok


async def _async_update_options(hass: HomeAssistant, entry: HisenseVidaaConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _get_coordinators(hass: HomeAssistant) -> list[HisenseVidaaCoordinator]:
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="no_tvs_configured",
        )
    return [
        entry.runtime_data.coordinator
        for entry in entries
        if entry.state.recoverable is False and entry.runtime_data is not None
    ]


async def _async_setup_services(hass: HomeAssistant) -> None:
    async def async_send_key(call: ServiceCall) -> None:
        key = call.data[ATTR_KEY]
        if key not in ALL_KEYS:
            raise ServiceValidationError(f"Unknown key '{key}'")
        for coordinator in _get_coordinators(hass):
            try:
                await coordinator.async_send_key(key)
            except Exception as err:  # noqa: BLE001
                raise HomeAssistantError("Failed to send key to TV") from err

    async def async_launch_app(call: ServiceCall) -> None:
        app = call.data[ATTR_APP]
        for coordinator in _get_coordinators(hass):
            try:
                await coordinator.async_launch_app(app)
            except Exception as err:  # noqa: BLE001
                raise HomeAssistantError("Failed to launch app on TV") from err

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_KEY):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_KEY,
            async_send_key,
            schema=vol.Schema({vol.Required(ATTR_KEY): cv.string}),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_LAUNCH_APP):
        hass.services.async_register(
            DOMAIN,
            SERVICE_LAUNCH_APP,
            async_launch_app,
            schema=vol.Schema({vol.Required(ATTR_APP): cv.string}),
        )
