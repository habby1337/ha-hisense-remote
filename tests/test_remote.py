"""Tests for remote command normalization."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_APPS_PATH = (
    Path(__file__).parent.parent / "custom_components" / "hisense_vidaa" / "apps.py"
)
_SPEC = importlib.util.spec_from_file_location("hisense_vidaa_apps", _APPS_PATH)
assert _SPEC and _SPEC.loader
_APPS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_APPS)

normalize_commands = _APPS.normalize_commands


def test_normalize_single_string_command() -> None:
    assert normalize_commands("volume_down") == ["volume_down"]


def test_normalize_command_list() -> None:
    assert normalize_commands(["up", "center"]) == ["up", "center"]
