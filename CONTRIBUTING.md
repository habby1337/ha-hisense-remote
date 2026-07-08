# Contributing

## Workflow

1. Branch from `main`
2. Use [Conventional Commits](https://www.conventionalcommits.org/)
3. Open a PR and wait for CI to pass
4. Rebase-merge into `main`

## Development

```bash
mise trust
mise install
mise run deps
mise run check
```

## Releases

Releases are automated with [Release Please](https://github.com/googleapis/release-please). Do not bump versions manually.

| Commit type                                 | Version bump |
| ------------------------------------------- | ------------ |
| `fix:`                                      | patch        |
| `feat:`                                     | minor        |
| `BREAKING CHANGE` / `feat!:`                | major        |
| `docs:`, `chore:`, `ci:`, `test:`, `style:` | no release   |

After a releasable merge to `main`, Release Please opens a release PR. It is rebased automatically; merging it creates the tag and GitHub release.
