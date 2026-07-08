"""Tests for key mapping."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_KEYS_PATH = (
    Path(__file__).parent.parent / "custom_components" / "hisense_vidaa" / "keys.py"
)
_SPEC = importlib.util.spec_from_file_location("hisense_vidaa_keys", _KEYS_PATH)
assert _SPEC and _SPEC.loader
_KEYS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_KEYS)

REMOTE_CARD_ALIASES = _KEYS.REMOTE_CARD_ALIASES
is_valid_key = _KEYS.is_valid_key
resolve_key = _KEYS.resolve_key


def test_resolve_vidaa_key_constants() -> None:
    assert resolve_key("KEY_HOME") == "KEY_HOME"
    assert resolve_key("up") == "KEY_UP"


def test_resolve_universal_remote_aliases() -> None:
    for alias, target in REMOTE_CARD_ALIASES.items():
        assert resolve_key(alias) == resolve_key(target)


def test_resolve_common_remote_commands() -> None:
    assert resolve_key("center") == "KEY_OK"
    assert resolve_key("volume_up") == "KEY_VOLUMEUP"
    assert resolve_key("volume_mute") == "KEY_MUTE"
    assert resolve_key("play_pause") == "KEY_PLAY"


def test_is_valid_key() -> None:
    assert is_valid_key("KEY_HOME")
    assert is_valid_key("home")
    assert is_valid_key("volume_up")
