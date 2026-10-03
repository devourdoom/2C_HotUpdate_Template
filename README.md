# 2C HotUpdate Template

Automatically mirrors the latest official PvZ2C level bundles (Android, Android beta, iOS) and hosts them on your own GitHub Pages.

## Setup

1. Create a repo from this template.
2. `Settings -> Actions -> General -> Workflow permissions` -> **Read and write**.
3. `Actions -> Sync official levels -> Run workflow`.
4. `Settings -> Pages` -> branch `gh-pages`.
5. Point `JsonUpdateServerConfig` in `serverconfig.rton` at `https://<you>.github.io/<repo>/`.

## How it works

Every ~10 minutes `sync.yml` checks the latest version of each platform, downloads its official levels into `raw/<ad|ad_beta|ios>/<version>/`, and triggers `build.yml`, which publishes to `gh-pages`.

- `ad`: latest Android version from the official site
- `ad_beta`: newest version the beta server has a bundle for
- `ios`: latest App Store version

Add your own files to `raw/` and push: they get built too, and the sync never overwrites a file you edited.

## Config

`config.json`: `platforms` (`ad`, `ad_beta`, `ios`). Remove one to stop syncing it.
