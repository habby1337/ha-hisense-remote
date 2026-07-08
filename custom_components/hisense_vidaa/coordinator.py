"""Data update coordinator for Hisense VIDAA."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from vidaa.wol import wake_tv

from .client import HisenseVidaaClient
from .const import (
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_MAC,
    CONF_MODEL,
    CONF_SW_VERSION,
    DOMAIN,
    SCAN_INTERVAL,
    STATE_FAKE_SLEEP,
    VOLUME_REFRESH_DELAY,
)

_LOGGER = logging.getLogger(__name__)


class HisenseVidaaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate TV state and command handling."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: HisenseVidaaClient,
        entry: ConfigEntry,
    ) -> None:
        scan_interval = entry.options.get("scan_interval", SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )
        self.client = client
        self.entry = entry
        self._available = True
        self._device_info_fetched = False
        self._auth_failures = 0
        self._volume_refresh_task: asyncio.Task[None] | None = None

    @property
    def available(self) -> bool:
        """Return whether the TV is reachable."""
        return self._available

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest TV state."""
        try:
            if not self.client.is_connected:
                await self.client.disconnect()
                if not await self.client.connect(timeout=5):
                    self._available = False
                    raise UpdateFailed("Failed to connect to TV")

            self._available = True
            await self._async_update_device_info()

            state = await self.client.get_state(timeout=3)
            is_on = self._is_powered_on(state)

            volume: int | None = None
            is_muted = False
            if is_on:
                try:
                    volume = await self.client.get_volume(timeout=1)
                    is_muted = self.client.is_muted
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Volume read failed: %s", err)

            app, source = self._extract_media(state)
            return {
                "is_on": is_on,
                "state": state,
                "statetype": state.get("statetype") if state else None,
                "volume": volume,
                "is_muted": is_muted,
                "app": app,
                "source": source,
            }
        except UpdateFailed:
            raise
        except Exception as err:  # noqa: BLE001
            self._available = False
            if self._is_auth_error(err):
                self._auth_failures += 1
                if self._auth_failures >= 3:
                    raise ConfigEntryAuthFailed(
                        "Authentication failed. Please re-pair the TV."
                    ) from err
            raise UpdateFailed(f"Error communicating with TV: {err}") from err

    async def _async_update_device_info(self) -> None:
        """Populate device registry details once."""
        if self._device_info_fetched:
            return

        try:
            device_info = await self.client.get_device_info(timeout=5)
            if not device_info:
                return

            device_id = self.entry.data.get(CONF_DEVICE_ID) or self._extract_device_id(
                device_info
            )
            device_registry = dr.async_get(self.hass)
            device_entry = device_registry.async_get_device(
                identifiers={(DOMAIN, device_id)}
            ) or device_registry.async_get_device(
                identifiers={(DOMAIN, self.entry.entry_id)}
            )

            if device_entry:
                updates: dict[str, str] = {}
                model = device_info.get("model_name")
                sw_version = device_info.get("tv_version")
                name = device_info.get("tv_name")
                if model and model != device_entry.model:
                    updates["model"] = model
                if sw_version and sw_version != device_entry.sw_version:
                    updates["sw_version"] = sw_version
                if name and name != device_entry.name:
                    updates["name"] = name
                if updates:
                    device_registry.async_update_device(device_entry.id, **updates)

            new_data = dict(self.entry.data)
            if model := device_info.get("model_name"):
                new_data[CONF_MODEL] = model
            if sw_version := device_info.get("tv_version"):
                new_data[CONF_SW_VERSION] = sw_version
            if device_id:
                new_data[CONF_DEVICE_ID] = device_id
            self.hass.config_entries.async_update_entry(self.entry, data=new_data)
            self._device_info_fetched = True
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Error fetching device info: %s", err)

    @staticmethod
    def _is_powered_on(state: dict[str, Any] | None) -> bool:
        if not state:
            return False
        return state.get("statetype") != STATE_FAKE_SLEEP

    @staticmethod
    def _extract_media(state: dict[str, Any] | None) -> tuple[str | None, str | None]:
        if not state:
            return None, None

        statetype = state.get("statetype")
        if statetype == "app":
            app_key = state.get("name", "").lower()
            return HisenseVidaaClient.resolve_app_name(app_key), None
        if statetype == "sourceswitch":
            source = state.get("displayname") or state.get("sourcename")
            return None, source
        return None, None

    @staticmethod
    def _extract_device_id(device_info: dict[str, Any]) -> str | None:
        network_type = device_info.get("network_type", "")
        return (
            device_info.get(f"{network_type}0")
            or device_info.get("wlan0")
            or device_info.get("eth0")
        )

    @staticmethod
    def _is_auth_error(err: Exception) -> bool:
        message = str(err).lower()
        return any(token in message for token in ("auth", "unauthorized", "forbidden"))

    def _patch_data(self, **changes: Any) -> None:
        """Apply optimistic state updates without waiting for polling."""
        if self.data is None:
            return
        self.async_set_updated_data({**self.data, **changes})

    async def _async_refresh_volume(self, optimistic_volume: int | None = None) -> None:
        """Refresh volume quickly after a command to keep sliders in sync."""
        if optimistic_volume is not None:
            self._patch_data(volume=optimistic_volume)

        await asyncio.sleep(VOLUME_REFRESH_DELAY)
        try:
            volume = await self.client.get_volume(timeout=2)
            is_muted = self.client.is_muted
            self._patch_data(volume=volume, is_muted=is_muted)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Volume refresh failed: %s", err)

    def _schedule_volume_refresh(self, optimistic_volume: int | None = None) -> None:
        """Debounce rapid volume updates into a single refresh."""
        if self._volume_refresh_task and not self._volume_refresh_task.done():
            self._volume_refresh_task.cancel()

        async def _runner() -> None:
            await self._async_refresh_volume(optimistic_volume)

        self._volume_refresh_task = self.hass.async_create_task(_runner())

    async def async_turn_on(self) -> None:
        """Turn the TV on using Wake-on-LAN and power command."""
        mac = self.entry.data.get(CONF_MAC)
        if mac:
            host = self.entry.data.get(CONF_HOST, "")
            subnet = host.rsplit(".", 1)[0] if "." in host else None
            await self.hass.async_add_executor_job(wake_tv, mac, subnet)
        await self.client.power_on()
        await self.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the TV off."""
        await self.client.power_off()
        await self.async_request_refresh()

    async def async_volume_up(self) -> None:
        """Increase volume."""
        current = self.data.get("volume") if self.data else None
        optimistic = min(100, current + 1) if isinstance(current, int) else None
        await self.client.volume_up()
        self._schedule_volume_refresh(optimistic)

    async def async_volume_down(self) -> None:
        """Decrease volume."""
        current = self.data.get("volume") if self.data else None
        optimistic = max(0, current - 1) if isinstance(current, int) else None
        await self.client.volume_down()
        self._schedule_volume_refresh(optimistic)

    async def async_mute(self) -> None:
        """Toggle mute."""
        await self.client.mute()
        self._schedule_volume_refresh()

    async def async_set_volume(self, volume: int) -> None:
        """Set absolute volume."""
        clamped = max(0, min(100, volume))
        await self.client.set_volume(clamped)
        self._schedule_volume_refresh(clamped)

    async def async_select_source(self, source: str) -> None:
        """Select an input source."""
        await self.client.set_source(source)
        await self.async_request_refresh()

    async def async_send_key(self, key: str) -> None:
        """Send a remote key."""
        await self.client.send_key(key)

    async def async_launch_app(self, app_name: str) -> None:
        """Launch an application."""
        await self.client.launch_app(app_name)
        await self.async_request_refresh()

    async def async_get_apps(self) -> list[dict[str, Any]] | None:
        """Return installed apps."""
        return await self.client.get_apps()

    async def async_get_sources(self) -> list[dict[str, Any]] | None:
        """Return available input sources."""
        return await self.client.get_sources()
