"""Mirrors the official localization text (pvz2_l.txt) into text/<platform>/<version>/ (run by .github/workflows/sync.yml).

The CDN serves a tiny file_list.txt per platform that names the text file and the MD5 of its plaintext. We poll only that,
and download the big file when the listed hash differs from tracking/text.json.
Every change is saved as a new <version>_<revision>_<platform>.txt, nothing is overwritten.
"""
import argparse
import hashlib
import json
import os
import re
import socket
import time
import urllib.request
from base64 import b64decode
from datetime import datetime, timezone
from pathlib import Path

from compiledtext import decode

socket.setdefaulttimeout(20)

ROOT = Path(__file__).parent
CONFIG = ROOT / "config.json"
STATE = ROOT / "tracking" / "text.json"
LEVELS_STATE = ROOT / "tracking" / "levels.json"
COMMIT_MSG = ROOT / ".sync_message"

CDN = "https://pvz2cdn.ditwan.cn"
UA = {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14)"}


def fetch(url: str) -> bytes:
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as resp:
                return resp.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(3)


def remote_entry(platform: str) -> tuple[str, str]:
    """(file name, md5 of its plaintext) from the platform's file_list.txt."""
    blob = decode(b64decode(fetch(f"{CDN}/{platform}/res_release/file_list.txt").strip()))
    entry = json.loads(blob)["File"]
    name, md5 = Path(entry["Name"]).name, entry["Hash"].lower()
    if not re.fullmatch(r"[0-9a-f]{32}", md5):
        raise ValueError(f"unexpected hash in file_list: {md5!r}")
    return name, md5


def known_version(platform: str) -> str | None:
    """Newest game version we have levels for; informational only, never used to decide anything."""
    if not LEVELS_STATE.exists():
        return None
    vs = [k.split("/", 1)[1] for k in json.loads(LEVELS_STATE.read_text("utf-8")) if k.startswith(platform + "/")]
    return max(vs, key=lambda v: tuple(int(p) for p in v.split("."))) if vs else None


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = ap.parse_args()

    cfg = json.loads(CONFIG.read_text("utf-8"))
    state = json.loads(STATE.read_text("utf-8")) if STATE.exists() else {}
    log: list[str] = []

    for platform in cfg.get("text_platforms", ["ad", "ios"]):
        try:
            name, md5 = remote_entry(platform)
        except Exception as ex:
            print(f"  ! {platform}: file_list lookup failed: {ex}")
            continue

        prev = state.get(platform, {})
        print(f"{platform}: official {name} hash {md5[:12]}")
        if prev.get("hash") == md5 and (ROOT / prev.get("file", "")).is_file():
            continue

        try:
            plain = decode(b64decode(fetch(f"{CDN}/{platform}/res_release/{name}").strip()))
        except Exception as ex:
            print(f"  ! {platform}: download/decode of {name} failed: {ex}")
            continue
        if hashlib.md5(plain).hexdigest() != md5:
            # file_list and the file are published separately, so they can briefly disagree; try again next run
            print(f"  ! {platform}: {name} does not match its listed hash yet, skipping")
            continue

        version = known_version(platform) or "unknown"
        folder = ROOT / "text" / platform / version
        revs = [int(m.group(1)) for f in folder.glob(f"{version}_*_{platform}.txt") if (m := re.fullmatch(rf"{re.escape(version)}_(\d+)_{platform}\.txt", f.name))]
        rev = max(revs, default=0) + 1
        path = folder / f"{version}_{rev}_{platform}.txt"
        updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"{path.relative_to(ROOT).as_posix()}: {'official text changed' if prev else 'first sync'} (hash {md5[:12]})"
        if not args.dry_run:
            folder.mkdir(parents=True, exist_ok=True)
            path.write_bytes(plain)

        history = prev.get("history", []) + [{"hash": md5, "version": version, "revision": rev, "updated": updated}]
        state[platform] = {"hash": md5, "file": path.relative_to(ROOT).as_posix(), "version": version,
                           "revision": rev, "updated": updated, "history": history}
        log.append(line)

    if not log:
        print("no text changes.")
        return
    print("\n".join(log))
    if args.dry_run:
        return

    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n", "utf-8")
    if COMMIT_MSG.exists():  # sync_official already wrote one this run
        body = COMMIT_MSG.read_text("utf-8").split("\n", 1)[1]
        COMMIT_MSG.write_text("sync official levels and text\n" + body.rstrip("\n") + "\n" + "\n".join(log) + "\n", "utf-8")
    else:
        COMMIT_MSG.write_text("sync official text\n\n" + "\n".join(log) + "\n", "utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("### Official text sync\n" + "\n".join(f"- {l}" for l in log) + "\n")


if __name__ == "__main__":
    main()
