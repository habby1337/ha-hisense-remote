"""Shared entity base for Hisense VIDAA."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DEVICE_ID,
    CONF_MAC,
    CONF_MODEL,
    CONF_NAME,
    CONF_SW_VERSION,
    DEFAULT_NAME,
    DOMAIN,
    MANUFACTURER,
)
from .coordinator import HisenseVidaaCoordinator


class HisenseVidaaEntity(CoordinatorEntity[HisenseVidaaCoordinator]):
    """Base class for Hisense VIDAA entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HisenseVidaaCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._mac = entry.data.get(CONF_MAC)
        self._device_id = entry.data.get(CONF_DEVICE_ID) or self._mac

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information."""
        device_id = self._device_id or self._entry.entry_id
        info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=self._entry.data.get(CONF_NAME, DEFAULT_NAME),
            manufacturer=MANUFACTURER,
            model=self._entry.data.get(CONF_MODEL),
            sw_version=self._entry.data.get(CONF_SW_VERSION),
        )
        if self._mac:
            info["connections"] = {(CONNECTION_NETWORK_MAC, self._mac.lower())}
        return info
