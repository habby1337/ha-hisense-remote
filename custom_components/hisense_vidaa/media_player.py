"""Media player platform for Hisense VIDAA."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import HisenseVidaaCoordinator
from .entity import HisenseVidaaEntity

if TYPE_CHECKING:
    from . import HisenseVidaaConfigEntry

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HisenseVidaaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the media player platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([HisenseVidaaMediaPlayer(coordinator, entry)])


class HisenseVidaaMediaPlayer(HisenseVidaaEntity, MediaPlayerEntity):
    """Representation of a Hisense VIDAA media player."""

    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_name = None
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.PLAY_MEDIA
    )

    def __init__(
        self,
        coordinator: HisenseVidaaCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = (
            f"{self._device_id}_media_player"
            if self._device_id
            else f"{entry.entry_id}_media_player"
        )
        self._apps: list[dict[str, Any]] = []
        self._source_list: list[str] = []

    @property
    def available(self) -> bool:
        """Keep entity available so Wake-on-LAN power on still works."""
        return True

    @property
    def state(self) -> MediaPlayerState:
        if not self.coordinator.data or not self.coordinator.available:
            return MediaPlayerState.OFF
        if self.coordinator.data.get("is_on"):
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        if not self.coordinator.data:
            return None
        volume = self.coordinator.data.get("volume")
        if volume is None:
            return None
        return volume / 100.0

    @property
    def is_volume_muted(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("is_muted", False)

    @property
    def source(self) -> str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("source")

    @property
    def source_list(self) -> list[str]:
        return self._source_list

    @property
    def app_name(self) -> str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("app")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await self._async_update_sources()

    async def _async_update_sources(self) -> None:
        try:
            sources = await self.coordinator.async_get_sources()
            apps = await self.coordinator.async_get_apps()
            source_list: list[str] = []

            if sources:
                for source in sources:
                    if isinstance(source, dict):
                        name = source.get("sourcename") or source.get("name")
                        if name:
                            source_list.append(name)

            if apps:
                self._apps = apps
                for app in apps:
                    if isinstance(app, dict) and (name := app.get("name")):
                        if name not in source_list:
                            source_list.append(name)

            self._source_list = source_list
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Error updating sources: %s", err)

    async def async_turn_on(self) -> None:
        await self.coordinator.async_turn_on()

    async def async_turn_off(self) -> None:
        await self.coordinator.async_turn_off()

    async def async_volume_up(self) -> None:
        await self.coordinator.async_volume_up()

    async def async_volume_down(self) -> None:
        await self.coordinator.async_volume_down()

    async def async_mute_volume(self, mute: bool) -> None:
        if self.is_volume_muted != mute:
            await self.coordinator.async_mute()

    async def async_set_volume_level(self, volume: float) -> None:
        await self.coordinator.async_set_volume(int(volume * 100))

    async def async_select_source(self, source: str) -> None:
        for app in self._apps:
            if app.get("name") == source:
                await self.coordinator.async_launch_app(source)
                return
        await self.coordinator.async_select_source(source)

    async def async_media_play(self) -> None:
        await self.coordinator.async_send_key("KEY_PLAY")

    async def async_media_pause(self) -> None:
        await self.coordinator.async_send_key("KEY_PAUSE")

    async def async_media_stop(self) -> None:
        await self.coordinator.async_send_key("KEY_STOP")

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        if media_type == "app":
            await self.coordinator.async_launch_app(media_id)
