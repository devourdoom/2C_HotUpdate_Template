# 2C HotUpdate Template

Automatically mirrors the official PvZ2C level bundles and hosts them on your own GitHub Pages.

## Setup

1. Create a repo from this template.
2. `Settings -> Actions -> General -> Workflow permissions` -> **Read and write**.
3. `Actions -> Sync official levels -> Run workflow`.
4. `Settings -> Pages` -> branch `gh-pages`.
5. Point `JsonUpdateServerConfig` in `serverconfig.rton` at `https://<you>.github.io/<repo>/<variant>/`.

## How it works

Every ~10 minutes `sync.yml` checks the latest Android version (official site) and iOS version (App Store), downloads any new official levels into `raw/<variant>/<ad|ios>/<version>/`, and triggers `build.yml`, which publishes to `gh-pages`.

Add your own files to `raw/` and push: they get built too, and the sync never overwrites a file you edited.

## Config

`config.json`: `variants` (folders under `raw/`), `platforms` (`ad`, `ios`), `scan.patch_lookahead`.
