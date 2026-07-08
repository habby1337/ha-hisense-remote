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

## Protocol

This integration uses [vidaa-control](https://github.com/tombabolewski/vidaa-control) for MQTT-over-TLS on port `36669`. Authentication tokens are stored in `.hisense_vidaa_tokens.json` in the Home Assistant config directory.
