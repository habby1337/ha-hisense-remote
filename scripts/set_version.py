#!/usr/bin/env python3
"""Set the integration version across project metadata files."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "custom_components/hisense_vidaa/manifest.json"
PYPROJECT = ROOT / "pyproject.toml"
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def validate_version(version: str) -> str:
    version = version.removeprefix("v").strip()
    if not VERSION_PATTERN.fullmatch(version):
        msg = f"Invalid version '{version}'. Use SemVer MAJOR.MINOR.PATCH (e.g. 0.2.0)."
        raise ValueError(msg)
    return version


def update_manifest(version: str) -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["version"] = version
    MANIFEST.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def update_pyproject(version: str) -> None:
    content = PYPROJECT.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'^version = ".*"$',
        f'version = "{version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise RuntimeError("Could not update version in pyproject.toml")
    PYPROJECT.write_text(updated, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: set_version.py VERSION", file=sys.stderr)
        return 1

    try:
        version = validate_version(sys.argv[1])
        update_manifest(version)
        update_pyproject(version)
    except (ValueError, RuntimeError, json.JSONDecodeError) as err:
        print(err, file=sys.stderr)
        return 1

    print(f"Version set to {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
