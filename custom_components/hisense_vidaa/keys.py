"""Key mapping for Hisense VIDAA remotes and universal-remote-card."""

from __future__ import annotations

from vidaa.keys import ALL_KEYS
from vidaa.keys import get_key as _get_vidaa_key

# Extra aliases used by universal-remote-card Generic Remote platform.
REMOTE_CARD_ALIASES: dict[str, str] = {
    "center": "ok",
    "select": "ok",
    "return": "back",
    "play_pause": "play",
    "previous": "rewind",
    "next": "forward",
    "volume_up": "volumeup",
    "volume_down": "volumedown",
    "vol_up": "volumeup",
    "vol_down": "volumedown",
    "ch_up": "channelup",
    "ch_down": "channeldown",
}


def resolve_key(command: str) -> str:
    """Resolve a remote command name to a VIDAA key constant."""
    normalized = command.strip()
    if normalized.startswith("KEY_"):
        return normalized
    alias = REMOTE_CARD_ALIASES.get(normalized.lower(), normalized.lower())
    return _get_vidaa_key(alias)


def is_valid_key(key: str) -> bool:
    """Return whether the key is a known VIDAA key."""
    if key in ALL_KEYS:
        return True
    return resolve_key(key) in ALL_KEYS
