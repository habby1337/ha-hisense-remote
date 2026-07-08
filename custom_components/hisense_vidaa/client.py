"""Thin async wrapper around the vidaa-control protocol library."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from vidaa import APPS, AsyncVidaaTV, async_detect_protocol
from vidaa.config import TokenStorage
from vidaa.protocol import AuthMethod, get_auth_method

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
        enable_persistence: bool = True,
        auth_method: AuthMethod | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._mac_address = mac_address
        self._token_path = token_path
        self._enable_persistence = enable_persistence
        self._auth_method = auth_method
        self._tv = self._create_tv()

    @property
    def host(self) -> str:
        """Return the TV host."""
        return self._host

    @property
    def mac_address(self) -> str | None:
        """Return the MAC address used for dynamic auth."""
        return self._mac_address

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
        if self._token_path is not None and self._enable_persistence:
            storage = TokenStorage(self._token_path)

        return AsyncVidaaTV(
            host=self._host,
            port=self._port,
            mac_address=self._mac_address,
            use_dynamic_auth=True,
            enable_persistence=self._enable_persistence,
            storage=storage,
            auth_method=self._auth_method,
            auto_detect_protocol=self._auth_method is None,
        )

    def rebuild(self) -> None:
        """Recreate the underlying client after connection parameters change."""
        self._tv = self._create_tv()

    async def connect(self, timeout: float = TIMEOUT_CONNECT) -> bool:
        """Connect to the TV, reconnecting only when needed."""
        if self._tv.is_connected:
            return True
        return await self._tv.async_connect(timeout=timeout)

    async def ensure_connected(self, timeout: float = TIMEOUT_CONNECT) -> bool:
        """Ensure the TV connection is active."""
        return await self.connect(timeout=timeout)

    async def disconnect(self) -> None:
        """Disconnect from the TV."""
        await self._tv.async_disconnect()

    async def detect_protocol(self) -> int | None:
        """Detect the TV transport protocol version from UPnP."""
        return await async_detect_protocol(self._host)

    async def apply_detected_auth_method(self) -> AuthMethod | None:
        """Rebuild the client using the detected transport protocol."""
        protocol_version = await self.detect_protocol()
        auth_method = get_auth_method(protocol_version)
        if auth_method is self._auth_method:
            return auth_method

        await self.disconnect()
        self._auth_method = auth_method
        self.rebuild()
        _LOGGER.debug(
            "Using %s auth for %s (protocol=%s)",
            auth_method.value,
            self._host,
            protocol_version,
        )
        return auth_method

    async def clear_saved_credentials(self) -> None:
        """Remove stored credentials for this TV before a new pairing attempt."""
        if self._token_path is None:
            return

        def _clear() -> None:
            storage = TokenStorage(self._token_path)
            storage.delete_token(
                device_id=self._mac_address,
                host=self._host,
                port=self._port,
            )

        await asyncio.get_running_loop().run_in_executor(None, _clear)
        await self.disconnect()
        self.rebuild()

    async def start_pairing(self) -> bool:
        """Start PIN pairing on the TV."""
        return await self._tv.async_start_pairing()

    async def authenticate(self, pin: str, timeout: float = TIMEOUT_COMMAND) -> bool:
        """Authenticate using the PIN shown on the TV."""
        if not await self.ensure_connected(timeout=timeout):
            _LOGGER.warning("Cannot authenticate because the TV is not connected")
            return False
        return await self._tv.async_authenticate(pin, timeout=timeout)

    async def get_tv_info(self, timeout: float = TIMEOUT_COMMAND) -> dict[str, Any] | None:
        """Return TV hardware info, including device identifiers."""
        return await self._tv.async_get_tv_info(timeout=timeout)

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
