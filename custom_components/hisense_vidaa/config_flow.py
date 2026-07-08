"""Config flow for Hisense VIDAA."""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import ssdp
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)
from vidaa.wol import get_mac_from_ip

from .client import HisenseVidaaClient
from .const import (
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_MAC,
    CONF_MODEL,
    CONF_NAME,
    CONF_PORT,
    CONF_SW_VERSION,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DOMAIN,
    SCAN_INTERVAL,
    TIMEOUT_CONNECT,
    TOKEN_FILE,
)

_LOGGER = logging.getLogger(__name__)
_HOST_PATTERN = re.compile(r"^[\w.\-]+$")
_MAC_PATTERN = re.compile(r"([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}")


def _normalize_mac(mac: str | None) -> str | None:
    if not mac:
        return None
    return mac.upper().replace("-", ":")


def _extract_mac_from_device_info(device_info: dict[str, Any] | None) -> str | None:
    if not device_info:
        return None

    network_type = device_info.get("network_type", "")
    mac = device_info.get(f"{network_type}0") or device_info.get(
        "wlan0"
    ) or device_info.get("eth0")
    if mac and _MAC_PATTERN.match(mac):
        return _normalize_mac(mac)
    return None


def _extract_mac_from_tv_info(tv_info: dict[str, Any] | None) -> str | None:
    if not tv_info:
        return None

    for key in ("deviceid", "device_id", "uuid", "mac"):
        value = tv_info.get(key)
        if isinstance(value, str) and _MAC_PATTERN.match(value):
            return _normalize_mac(value)
    return None


def _normalize_pin(pin: str) -> str | None:
    normalized = pin.strip()
    if normalized.isdigit() and len(normalized) == 4:
        return normalized
    return None


class HisenseVidaaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hisense VIDAA."""

    VERSION = 1
    MAX_PIN_ATTEMPTS = 5

    def __init__(self) -> None:
        self._host: str | None = None
        self._port: int = DEFAULT_PORT
        self._name: str = DEFAULT_NAME
        self._mac: str | None = None
        self._device_id: str | None = None
        self._model: str | None = None
        self._sw_version: str | None = None
        self._pin_attempts = 0
        self._client: HisenseVidaaClient | None = None

    def _token_path(self) -> Path:
        return Path(self.hass.config.config_dir) / TOKEN_FILE

    async def _async_cleanup_client(self) -> None:
        if self._client:
            try:
                await self._client.disconnect()
            except Exception:  # noqa: BLE001
                pass
            self._client = None

    async def _async_resolve_mac(self) -> str | None:
        if not self._host:
            return None
        try:
            loop = asyncio.get_running_loop()
            mac = await loop.run_in_executor(None, get_mac_from_ip, self._host)
            return _normalize_mac(mac)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Could not resolve MAC from ARP: %s", err)
            return None

    async def _async_create_client(self) -> HisenseVidaaClient:
        return HisenseVidaaClient(
            host=self._host or "",
            port=self._port,
            mac_address=self._mac,
            token_path=self._token_path(),
        )

    async def _async_prepare_pairing_client(self) -> bool:
        """Connect with the right MAC and auth method for PIN pairing."""
        if not self._mac:
            self._mac = await self._async_resolve_mac()

        await self._async_cleanup_client()
        self._client = await self._async_create_client()
        await self._client.clear_saved_credentials()

        if not await self._client.connect(timeout=TIMEOUT_CONNECT):
            return False

        device_info = await self._client.get_device_info(timeout=5)
        await self._async_apply_device_info(device_info)

        if not self._mac:
            tv_info = await self._client.get_tv_info(timeout=5)
            info_mac = _extract_mac_from_tv_info(tv_info)
            if info_mac:
                self._mac = info_mac
                self._device_id = info_mac

        if self._mac and self._mac != self._client.mac_address:
            await self._client.disconnect()
            self._client = await self._async_create_client()
            await self._client.clear_saved_credentials()
            if not await self._client.connect(timeout=TIMEOUT_CONNECT):
                return False

        await self._client.apply_detected_auth_method()
        return await self._client.connect(timeout=TIMEOUT_CONNECT)

    async def _async_begin_pairing(self) -> ConfigFlowResult:
        if not await self._async_prepare_pairing_client():
            await self._async_cleanup_client()
            return self.async_abort(reason="cannot_connect")

        if self._mac:
            self._device_id = self._mac
        await self._async_set_unique_id()

        if not await self._client.start_pairing():
            await self._async_cleanup_client()
            return self.async_abort(reason="cannot_connect")

        await asyncio.sleep(1)
        return await self.async_step_pair()

    async def _async_apply_device_info(self, device_info: dict[str, Any] | None) -> None:
        if not device_info:
            return
        self._name = device_info.get("tv_name") or self._name
        self._model = device_info.get("model_name") or self._model
        self._sw_version = device_info.get("tv_version") or self._sw_version
        info_mac = _extract_mac_from_device_info(device_info)
        if info_mac:
            self._mac = info_mac
            self._device_id = info_mac

    async def _async_set_unique_id(self) -> None:
        if not self._device_id:
            return
        await self.async_set_unique_id(self._device_id.replace(":", "").lower())
        self._abort_if_unique_id_configured(
            updates={CONF_HOST: self._host, CONF_PORT: self._port}
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual setup."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            if not _HOST_PATTERN.match(host):
                errors["base"] = "invalid_host"
            else:
                self._host = host
                self._port = user_input.get(CONF_PORT, DEFAULT_PORT)
                self._mac = await self._async_resolve_mac()
                try:
                    return await self._async_begin_pairing()
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Connection error: %s", err)
                    errors["base"] = "cannot_connect"
                    await self._async_cleanup_client()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )

    async def async_step_pair(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle PIN pairing."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._pin_attempts += 1
            if self._pin_attempts > self.MAX_PIN_ATTEMPTS:
                await self._async_cleanup_client()
                return self.async_abort(reason="too_many_attempts")

            if not self._client:
                errors["base"] = "cannot_connect"
            else:
                try:
                    pin = _normalize_pin(user_input["pin"])
                    if pin is None:
                        errors["base"] = "invalid_pin"
                    elif not self._client.is_connected:
                        if not await self._client.ensure_connected(timeout=TIMEOUT_CONNECT):
                            errors["base"] = "cannot_connect"
                        elif not await self._client.start_pairing():
                            errors["base"] = "cannot_connect"
                        else:
                            await asyncio.sleep(1)
                            errors["base"] = "pin_expired"
                    elif await self._client.authenticate(pin, timeout=15):
                        device_info = await self._client.get_device_info(timeout=5)
                        await self._async_apply_device_info(device_info)
                        await self._client.disconnect()
                        self._client = None
                        await self._async_set_unique_id()
                        data = {
                            CONF_HOST: self._host,
                            CONF_PORT: self._port,
                            CONF_NAME: self._name,
                            CONF_MAC: self._mac,
                            CONF_DEVICE_ID: self._device_id,
                            CONF_MODEL: self._model,
                            CONF_SW_VERSION: self._sw_version,
                        }
                        if self.source == config_entries.SOURCE_REAUTH:
                            return self.async_update_reload_and_abort(
                                self._get_reauth_entry(),
                                data=data,
                            )
                        return self.async_create_entry(title=self._name, data=data)
                    else:
                        errors["base"] = "invalid_pin"
                        if await self._client.ensure_connected(timeout=TIMEOUT_CONNECT):
                            await self._client.start_pairing()
                            await asyncio.sleep(1)
                except Exception as err:  # noqa: BLE001
                    _LOGGER.exception("Pairing failed: %s", err)
                    errors["base"] = "pairing_failed"

        return self.async_show_form(
            step_id="pair",
            data_schema=vol.Schema({vol.Required("pin"): str}),
            errors=errors,
            description_placeholders={
                "name": self._name,
                "host": self._host or "",
            },
        )

    async def async_step_ssdp(
        self, discovery_info: ssdp.SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle SSDP discovery."""
        model_desc = discovery_info.upnp.get("modelDescription", "")
        if not any(
            line.strip().startswith("vidaa_support=1")
            for line in model_desc.split("\n")
            if "=" in line
        ):
            return self.async_abort(reason="not_vidaa_tv")

        host = discovery_info.ssdp_headers.get("_host") or discovery_info.ssdp_location
        if host and "://" in host:
            from urllib.parse import urlparse

            host = urlparse(host).hostname
        if not host:
            return self.async_abort(reason="no_host")

        self._host = host
        self._name = discovery_info.upnp.get("friendlyName", DEFAULT_NAME)
        usn = discovery_info.ssdp_usn
        if usn:
            unique_id = usn.split("::")[0].replace("uuid:", "")
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured(updates={CONF_HOST: self._host})
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm SSDP discovery."""
        if user_input is not None:
            self._mac = await self._async_resolve_mac()
            try:
                return await self._async_begin_pairing()
            except Exception:  # noqa: BLE001
                _LOGGER.exception("SSDP pairing failed")
                await self._async_cleanup_client()
                return self.async_abort(reason="cannot_connect")

        return self.async_show_form(
            step_id="confirm",
            description_placeholders={
                "name": self._name,
                "host": self._host or "",
            },
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthentication."""
        self._host = entry_data[CONF_HOST]
        self._port = entry_data.get(CONF_PORT, DEFAULT_PORT)
        self._mac = entry_data.get(CONF_MAC)
        self._device_id = entry_data.get(CONF_DEVICE_ID)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauthentication."""
        if user_input is not None:
            try:
                return await self._async_begin_pairing()
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Reauth failed")
                await self._async_cleanup_client()
                return self.async_abort(reason="cannot_connect")

        return self.async_show_form(
            step_id="reauth_confirm",
            description_placeholders={"host": self._host or ""},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return HisenseVidaaOptionsFlow()


class HisenseVidaaOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get("scan_interval", SCAN_INTERVAL)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("scan_interval", default=current_interval): NumberSelector(
                        NumberSelectorConfig(
                            min=10,
                            max=300,
                            step=5,
                            mode=NumberSelectorMode.SLIDER,
                            unit_of_measurement="seconds",
                        )
                    ),
                }
            ),
        )
