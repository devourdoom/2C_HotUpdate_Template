# 2C HotUpdate Template

Automatically mirrors the latest official PvZ2C level bundles (Android, Android beta, iOS) and hosts them on your own GitHub Pages.

## Setup

1. Create a repo from this template.
2. `Settings -> Actions -> General -> Workflow permissions` -> **Read and write**.
3. `Actions -> Sync official levels -> Run workflow`.
4. `Settings -> Pages` -> branch `gh-pages`.
5. Point `JsonUpdateServerConfig` in `serverconfig.rton` at `https://<you>.github.io/<repo>/`.

## How it works

`sync.yml` runs on a 15-minute schedule (best effort, see below) and checks the latest version of each platform, downloads its official levels into `json/<ad|ad_beta|ios>/<version>/`, and triggers `build.yml`, which publishes to `gh-pages`.

- `ad`: latest Android version from the official site
- `ad_beta`: newest version the beta server has a bundle for
- `ios`: latest App Store version

Add your own files to `json/` or `text/` and push: they get built too, and the sync never overwrites a file you edited.

## Localization text

The game's text (`pvz2_l.txt`) lives at fixed CDN URLs, next to a tiny `file_list.txt` that holds the MD5 of the current text. The sync (`sync_text.py`) checks only that file, separately for `ad` and `ios` (iOS can update first), and downloads the text only when the hash changed. No version number is involved.

- Every official change is saved as a new file, `text/<ad|ios>/<version>/<version>_<revision>_<platform>.txt` (e.g. `text/ios/4.2.6/4.2.6_2_ios.txt`); nothing is overwritten. The revision counts up within a game version.
- The build publishes the newest file per platform as `pvz2_l.txt`. To customize, edit the newest file; a later official change adds a new revision you merge by hand.
- `tracking/text.json` records, per platform, the current hash and a history of every hash with its version, revision and detection date.
- `tracking/levels.json` is the same for levels.
- The build publishes the re-encoded text and a matching `file_list.txt` to `hotupdate/<ad|ios>/res_release/` on GitHub Pages.

## Config

`config.json`: `platforms` (`ad`, `ad_beta`, `ios`) for levels and optional `text_platforms` (default `ad`, `ios`) for text. Remove one to stop syncing it.

## Sync timing

GitHub heavily throttles scheduled workflows, especially on low-activity repos: in practice runs can be hours apart, not minutes. If you need faster updates, trigger `Sync official levels` yourself (`Actions -> Run workflow`), or call it from an external scheduler such as cron-job.org via the `workflow_dispatch` REST endpoint.
