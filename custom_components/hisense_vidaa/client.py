"""Thin async wrapper around the vidaa-control protocol library."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from vidaa import APPS, AsyncVidaaTV
from vidaa.config import TokenStorage

from .const import DEFAULT_PORT, TIMEOUT_COMMAND, TIMEOUT_CONNECT

_LOGGER = logging.getLogger(__name__)


class HisenseVidaaClient:
    """Manage a single TV connection with idempotent lifecycle methods."""

    def __init__(
        self,
        host: str,
        *,
        port: int = DEFAULT_PORT,
        mac_address: str | None = None,
        token_path: Path | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._mac_address = mac_address
        self._token_path = token_path
        self._tv = self._create_tv()

    @property
    def host(self) -> str:
        """Return the TV host."""
        return self._host

    @property
    def is_connected(self) -> bool:
        """Return whether the underlying client is connected."""
        return self._tv.is_connected

    @property
    def is_muted(self) -> bool:
        """Return the muted state reported by the TV client."""
        return self._tv.is_muted

    def _create_tv(self) -> AsyncVidaaTV:
        storage = None
        if self._token_path is not None:
            storage = TokenStorage(self._token_path)

        return AsyncVidaaTV(
            host=self._host,
            port=self._port,
            mac_address=self._mac_address,
            use_dynamic_auth=True,
            enable_persistence=self._token_path is not None,
            storage=storage,
        )

    async def connect(self, timeout: float = TIMEOUT_CONNECT) -> bool:
        """Connect to the TV, reconnecting only when needed."""
        if self._tv.is_connected:
            return True
        return await self._tv.async_connect(timeout=timeout)

    async def disconnect(self) -> None:
        """Disconnect from the TV."""
        await self._tv.async_disconnect()

    async def start_pairing(self) -> None:
        """Start PIN pairing on the TV."""
        await self._tv.async_start_pairing()

    async def authenticate(self, pin: str, timeout: float = TIMEOUT_COMMAND) -> bool:
        """Authenticate using the PIN shown on the TV."""
        return await self._tv.async_authenticate(pin, timeout=timeout)

    async def get_device_info(self, timeout: float = TIMEOUT_COMMAND) -> dict[str, Any] | None:
        """Return device information from the TV."""
        return await self._tv.async_get_device_info(timeout=timeout)

    async def get_state(self, timeout: float = TIMEOUT_COMMAND) -> dict[str, Any] | None:
        """Return the current TV state."""
        return await self._tv.async_get_state(timeout=timeout)

    async def get_volume(self, timeout: float = TIMEOUT_COMMAND) -> int | None:
        """Return the current volume level (0-100)."""
        return await self._tv.async_get_volume(timeout=timeout)

    async def get_apps(self) -> list[dict[str, Any]] | None:
        """Return installed apps."""
        return await self._tv.async_get_apps()

    async def get_sources(self) -> list[dict[str, Any]] | None:
        """Return available input sources."""
        return await self._tv.async_get_sources()

    async def power_on(self) -> None:
        """Power on the TV."""
        await self._tv.async_power_on()

    async def power_off(self) -> None:
        """Power off the TV."""
        await self._tv.async_power_off()

    async def volume_up(self) -> None:
        """Increase volume."""
        await self._tv.async_volume_up()

    async def volume_down(self) -> None:
        """Decrease volume."""
        await self._tv.async_volume_down()

    async def mute(self) -> None:
        """Toggle mute."""
        await self._tv.async_mute()

    async def set_volume(self, volume: int) -> None:
        """Set absolute volume (0-100)."""
        await self._tv.async_set_volume(volume)

    async def set_source(self, source: str) -> None:
        """Select an input source."""
        await self._tv.async_set_source(source)

    async def send_key(self, key: str) -> None:
        """Send a remote key."""
        await self._tv.async_send_key(key)

    async def launch_app(self, app_name: str) -> None:
        """Launch an application."""
        await self._tv.async_launch_app(app_name)

    @staticmethod
    def resolve_app_name(app_key: str) -> str:
        """Resolve an app key to a display name."""
        normalized = app_key.lower()
        if normalized in APPS:
            return APPS[normalized].get("name", app_key)
        return app_key.capitalize()
