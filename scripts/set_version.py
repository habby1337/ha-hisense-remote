#!/usr/bin/env python3
"""Set the integration version in manifest.json for HACS and Home Assistant."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MANIFEST = Path(__file__).resolve().parents[1] / "custom_components/hisense_vidaa/manifest.json"
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: set_version.py VERSION", file=sys.stderr)
        return 1

    version = sys.argv[1].removeprefix("v").strip()
    if not VERSION_PATTERN.fullmatch(version):
        print(f"Invalid version '{version}'. Use SemVer MAJOR.MINOR.PATCH.", file=sys.stderr)
        return 1

    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        data["version"] = version
        MANIFEST.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except json.JSONDecodeError as err:
        print(err, file=sys.stderr)
        return 1

    print(f"Version set to {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
