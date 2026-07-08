# Hisense VIDAA for Home Assistant

Home Assistant custom integration for Hisense and VIDAA smart TVs. Communicates directly with the TV's built-in MQTT-over-TLS broker on port `36669` — no cloud, no external MQTT bridge.

## Features

- **Media player** with reliable volume control (`volume_set`, `volume_up`, `volume_down`, mute)
- **Remote** entity compatible with [Universal Remote Card](https://github.com/Nerwyn/universal-remote-card)
- **PIN pairing** with persisted authentication tokens
- **SSDP auto-discovery** for supported TVs
- **Wake-on-LAN** power on support
- **App launching** and input source selection

## Installation

### HACS (recommended)

[![Open Hisense VIDAA in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=habby1337&repository=ha-hisense-remote&category=integration)

1. Add this repository as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories/) in HACS
2. Install **Hisense VIDAA**
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → Add Integration → Hisense VIDAA**

### Manual

Copy `custom_components/hisense_vidaa/` into your `config/custom_components/` directory and restart Home Assistant.

## Setup

1. Ensure your TV is powered on and connected to the same network as Home Assistant
2. Add the integration via IP address or SSDP discovery
3. Enter the PIN shown on your TV screen
4. Entities are created automatically:
   - `media_player.<tv_name>`
   - `remote.<tv_name>_remote`

## Volume control

Volume is a first-class feature of this integration:

- `media_player.volume_set` sets absolute volume (0.0–1.0)
- `volume_level` is updated optimistically after commands, then confirmed from the TV
- This keeps volume sliders in Lovelace cards stable without jumping back

## Universal Remote Card

Install [Universal Remote Card](https://github.com/Nerwyn/universal-remote-card) via HACS, then use the **Generic Remote** platform with your entities.

[![Open Universal Remote Card in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=universal-remote-card&owner=Nerwyn&category=Plugin)

A ready-to-use example is in [`examples/universal-remote-card.yaml`](examples/universal-remote-card.yaml).

Minimal configuration:

```yaml
type: custom:universal-remote-card
platform: Generic Remote
remote_id: remote.living_room_remote
media_player_id: media_player.living_room
rows:
  - - power
  - - volume_up
    - slider
    - volume_down
  - - up
  - - left
    - center
    - right
  - - down
  - - home
    - back
custom_actions:
  - type: slider
    name: slider
    range: [0, 1]
    step: 0.01
    value_attribute: volume_level
    tap_action:
      action: perform-action
      perform_action: media_player.volume_set
      target:
        entity_id: media_player.living_room
      data:
        volume_level: "{{ value | float }}"
    entity_id: media_player.living_room
    vertical: true
    icon: mdi:volume-high
```

The remote accepts both VIDAA key constants (`KEY_HOME`) and friendly names used by Generic Remote (`home`, `center`, `volume_up`).

## Services

| Service                    | Description                                       |
| -------------------------- | ------------------------------------------------- |
| `hisense_vidaa.send_key`   | Send any remote key (e.g. `KEY_HOME`, `KEY_MUTE`) |
| `hisense_vidaa.launch_app` | Launch an app by name (e.g. `netflix`, `youtube`) |

## Options

- **Polling interval** — how often the TV state is refreshed (default: 30 seconds)

## License

MIT
