# Contributing

## Development environment

This project uses [mise](https://mise.jdx.dev/) for Python and virtualenv management.

```bash
mise trust
mise install
mise run deps
mise run check
```

## HACS validation

The CI workflow runs hassfest, HACS validation, ruff and pytest.

For HACS checks to pass, the GitHub repository needs topics (`home-assistant`, `hacs`, `homeassistant`) and a brand icon at `custom_components/hisense_vidaa/brand/icon.png`.

## Versioning

HACS and Home Assistant read the version from `custom_components/hisense_vidaa/manifest.json`. That file is the single source of truth.

### How HACS uses versions

- **With GitHub releases** (recommended): HACS offers the latest releases plus the default branch. The release tag must be `vX.Y.Z` and match `manifest.json` ([HACS docs](https://www.hacs.xyz/docs/publish/start/#versions)).
- **Without releases**: HACS installs from `main` and shows the `manifest.json` version.

Use [Semantic Versioning](https://semver.org/):

- `0.x.y` while the integration is still evolving
- `1.0.0` when the public API and config flow are stable

### Release workflow

1. Merge changes on `main`
2. Bump the version:

   ```bash
   mise run version -- 0.2.0
   ```

3. Commit:

   ```bash
   git add custom_components/hisense_vidaa/manifest.json pyproject.toml
   git commit -m "chore(release): bump version to 0.2.0"
   ```

4. Tag and push:

   ```bash
   git tag v0.2.0
   git push origin main
   git push origin v0.2.0
   ```

Pushing the tag triggers `.github/workflows/release.yml`, which validates that `v0.2.0` matches `manifest.json` and creates the GitHub release.

## Protocol

This integration uses [vidaa-control](https://github.com/tombabolewski/vidaa-control) for MQTT-over-TLS on port `36669`. Authentication tokens are stored in `.hisense_vidaa_tokens.json` in the Home Assistant config directory.
