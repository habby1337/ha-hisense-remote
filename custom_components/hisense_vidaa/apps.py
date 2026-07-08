"""App and input helpers for remote commands and media sources."""

from __future__ import annotations

from typing import Any

from vidaa.topics import APPS, SOURCE_MAP

APP_ALIASES: dict[str, str] = {
    "netflix": "netflix",
    "youtube": "youtube",
    "amazon": "amazon",
    "prime": "amazon",
    "primevideo": "amazon",
    "disney": "disney",
    "disney+": "disney+",
    "disneyplus": "disney",
    "tubi": "tubi",
}

SOURCE_ALIASES: dict[str, str] = {
    "tv": "tv",
    "dtv": "tv",
    "antenna": "tv",
    "av": "av",
    "aux": "av",
    "component": "component",
    "hdmi": "hdmi1",
    "hdmi1": "hdmi1",
    "hdmi 1": "hdmi1",
    "hdmi2": "hdmi2",
    "hdmi 2": "hdmi2",
    "hdmi3": "hdmi3",
    "hdmi 3": "hdmi3",
    "hdmi4": "hdmi4",
    "hdmi 4": "hdmi4",
}


def normalize_command(command: str) -> str:
    """Normalize a remote command name."""
    return command.strip().lower().replace("_", " ")


def resolve_app_command(command: str) -> str | None:
    """Return the app key if the command launches a known app."""
    normalized = normalize_command(command)
    compact = normalized.replace(" ", "")
    if compact in APP_ALIASES:
        return APP_ALIASES[compact]
    if normalized in APP_ALIASES:
        return APP_ALIASES[normalized]
    if compact in APPS:
        return compact
    if normalized in APPS:
        return normalized
    return None


def resolve_source_command(command: str) -> str | None:
    """Return the source key if the command switches a known input."""
    normalized = normalize_command(command)
    compact = normalized.replace(" ", "")
    if compact in SOURCE_ALIASES:
        return SOURCE_ALIASES[compact]
    if normalized in SOURCE_ALIASES:
        return SOURCE_ALIASES[normalized]
    if compact in SOURCE_MAP:
        return compact
    if normalized in SOURCE_MAP:
        return normalized
    return None


def match_source_name(command: str, sources: list[dict[str, Any]]) -> str | None:
    """Match a command against source names reported by the TV."""
    normalized = normalize_command(command).replace(" ", "")
    for source in sources:
        for field in ("sourcename", "displayname", "name"):
            value = source.get(field)
            if not isinstance(value, str):
                continue
            candidate = value.lower().replace(" ", "")
            if candidate == normalized or normalized in candidate:
                return value
    return None
