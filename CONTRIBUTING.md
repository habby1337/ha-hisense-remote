# Contributing

## Branching model

`main` is protected and must receive changes only through pull requests.

1. Create a feature branch from `main`
2. Use [Conventional Commits](https://www.conventionalcommits.org/)
3. Open a PR and wait for CI (`validate`) to pass
4. Merge the PR into `main`

`main` is protected on GitHub and requires CI to pass before merge.

## Development environment

This project uses [mise](https://mise.jdx.dev/) for Python and virtualenv management.

```bash
mise trust
mise install
mise run deps
mise run check
```

## Versioning and releases

Releases are automated with [Release Please](https://github.com/googleapis/release-please) on every merge to `main`.

| Commit type                                 | Version bump              |
| ------------------------------------------- | ------------------------- |
| `fix:`                                      | patch (`1.0.0` → `1.0.1`) |
| `feat:`                                     | minor (`1.0.0` → `1.1.0`) |
| `BREAKING CHANGE` / `feat!:`                | major (`1.0.0` → `2.0.0`) |
| `docs:`, `chore:`, `ci:`, `test:`, `style:` | no release                |

### How it works

1. A merge to `main` triggers the **Release** workflow (`github-actions[bot]`)
2. Release Please opens or updates a release PR (`autorelease: pending` label)
3. The release PR bumps `manifest.json`, `.release-please-manifest.json`, and `CHANGELOG.md`
4. When CI passes, the release PR is auto-merged
5. On merge, Release Please creates tag `vX.Y.Z` and a GitHub release

HACS reads the version from `custom_components/hisense_vidaa/manifest.json` and uses GitHub releases when available.

### GitHub settings required

- **Allow auto-merge** enabled (Settings → General → Pull Requests)
- **Signed commits** not required for `github-actions[bot]` (or disabled in the branch ruleset)

### Initial version

The integration targets **1.0.0** as its first public release. `manifest.json` already reflects that version; `.release-please-manifest.json` starts empty so Release Please treats nothing as released yet.

After the first releasable merge to `main`, Release Please opens a release PR (typically `1.0.0` or the next semver from conventional commits). Merging it creates tag `v1.0.0` and the GitHub release.

## HACS validation

The CI workflow runs hassfest, HACS validation, ruff and pytest.

For HACS checks to pass, the GitHub repository needs topics (`home-assistant`, `hacs`, `homeassistant`) and a brand icon at `custom_components/hisense_vidaa/brand/icon.png`.

## Protocol

This integration uses [vidaa-control](https://github.com/tombabolewski/vidaa-control) for MQTT-over-TLS on port `36669`. Authentication tokens are stored in `.hisense_vidaa_tokens.json` in the Home Assistant config directory.
