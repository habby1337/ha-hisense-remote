# Contributing

## Branching model

`main` is protected and must receive changes only through pull requests.

1. Create a feature branch from `main`
2. Use [Conventional Commits](https://www.conventionalcommits.org/)
3. Open a PR and wait for CI (`validate`) to pass
4. Merge the PR into `main`

Apply the repository ruleset once (repository admin):

```bash
gh api repos/habby1337/ha-hisense-remote/rulesets --method POST --input .github/rulesets/main.json
```

The ruleset blocks direct pushes to `main`, requires CI to pass, and allows `github-actions[bot]` to push release commits.

## Development environment

This project uses [mise](https://mise.jdx.dev/) for Python and virtualenv management.

```bash
mise trust
mise install
mise run deps
mise run check
```

## Versioning and releases

Releases are automated with [semantic-release](https://semantic-release.gitbook.io/) on every merge to `main`.

| Commit type                                 | Version bump                             |
| ------------------------------------------- | ---------------------------------------- |
| `fix:`                                      | patch (`0.1.0` → `0.1.1`)                |
| `feat:`                                     | minor (`0.1.0` → `0.2.0`)                |
| `BREAKING CHANGE` / `feat!:`                | minor while on `0.x`, major from `1.0.0` |
| `docs:`, `chore:`, `ci:`, `test:`, `style:` | no release                               |

On each releasable merge, the workflow:

1. Analyzes commits since the last tag
2. Updates `manifest.json`
3. Updates `CHANGELOG.md`
4. Creates commit `chore(release): X.Y.Z [skip ci]`
5. Creates tag `vX.Y.Z` and a GitHub release

HACS reads the version from `custom_components/hisense_vidaa/manifest.json` and uses GitHub releases when available.

### Bootstrap the first release

Before the first automated release, tag the current `main` manually:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The next releasable merge after that will bump from `0.1.0`.

## HACS validation

The CI workflow runs hassfest, HACS validation, ruff and pytest.

For HACS checks to pass, the GitHub repository needs topics (`home-assistant`, `hacs`, `homeassistant`) and a brand icon at `custom_components/hisense_vidaa/brand/icon.png`.

## Protocol

This integration uses [vidaa-control](https://github.com/tombabolewski/vidaa-control) for MQTT-over-TLS on port `36669`. Authentication tokens are stored in `.hisense_vidaa_tokens.json` in the Home Assistant config directory.
