"""Tests for app and source command resolution."""

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

match_source_name = _APPS.match_source_name
resolve_app_command = _APPS.resolve_app_command
resolve_source_command = _APPS.resolve_source_command


def test_resolve_app_commands() -> None:
    assert resolve_app_command("netflix") == "netflix"
    assert resolve_app_command("YouTube") == "youtube"
    assert resolve_app_command("prime") == "amazon"


def test_resolve_source_commands() -> None:
    assert resolve_source_command("hdmi 1") == "hdmi1"
    assert resolve_source_command("AV") == "av"
    assert resolve_source_command("dtv") == "tv"


def test_match_source_name() -> None:
    sources = [{"sourcename": "HDMI 1"}, {"displayname": "AV"}]
    assert match_source_name("hdmi1", sources) == "HDMI 1"
    assert match_source_name("av", sources) == "AV"


def test_match_source_name_skips_non_dict_entries() -> None:
    sources = ["HDMI 1", {"sourcename": "AV"}]
    assert match_source_name("av", sources) == "AV"
