"""Remote platform for Hisense VIDAA."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from homeassistant.components.remote import RemoteEntity, RemoteEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .apps import match_source_name, resolve_app_command, resolve_source_command
from .coordinator import HisenseVidaaCoordinator
from .entity import HisenseVidaaEntity
from .keys import resolve_key

if TYPE_CHECKING:
    from . import HisenseVidaaConfigEntry

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HisenseVidaaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the remote platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([HisenseVidaaRemote(coordinator, entry)])


class HisenseVidaaRemote(HisenseVidaaEntity, RemoteEntity):
    """Representation of a Hisense VIDAA remote."""

    _attr_name = "Remote"
    _attr_supported_features = RemoteEntityFeature.ACTIVITY

    def __init__(
        self,
        coordinator: HisenseVidaaCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = (
            f"{self._device_id}_remote"
            if self._device_id
            else f"{entry.entry_id}_remote"
        )
        self._activity_list: list[str] = []

    @property
    def available(self) -> bool:
        return self.coordinator.available

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("is_on", False)

    @property
    def current_activity(self) -> str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("app") or self.coordinator.data.get("source")

    @property
    def activity_list(self) -> list[str] | None:
        return self._activity_list or None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await self._async_update_activities()

    async def _async_update_activities(self) -> None:
        try:
            apps = await self.coordinator.async_get_apps()
            if apps:
                self._activity_list = [
                    app["name"] for app in apps if isinstance(app, dict) and app.get("name")
                ]
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Error updating activities: %s", err)

    async def async_turn_on(self, activity: str | None = None, **kwargs: Any) -> None:
        await self.coordinator.async_turn_on()
        if activity:
            await self.coordinator.async_launch_app(activity)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_turn_off()

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        num_repeats = kwargs.get("num_repeats", 1)
        delay_secs = kwargs.get("delay_secs", 0.2)

        for _ in range(num_repeats):
            for cmd in command:
                await self._async_dispatch_command(cmd)
            if delay_secs > 0:
                await asyncio.sleep(delay_secs)

    async def _async_dispatch_command(self, command: str) -> None:
        app_key = resolve_app_command(command)
        if app_key:
            await self.coordinator.async_launch_app(app_key)
            return

        source_key = resolve_source_command(command)
        if source_key:
            await self.coordinator.async_select_source(source_key)
            return

        sources = await self.coordinator.async_get_sources() or []
        matched_source = match_source_name(command, sources)
        if matched_source:
            await self.coordinator.async_select_source(matched_source)
            return

        apps = await self.coordinator.async_get_apps() or []
        normalized = command.strip().lower()
        for app in apps:
            name = app.get("name")
            if isinstance(name, str) and name.lower() == normalized:
                await self.coordinator.async_launch_app(name)
                return

        await self.coordinator.async_send_key(resolve_key(command))
