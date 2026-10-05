"""Packs plaintext level JSON into a level_shipping bundle. Usage: python main.py <cv> <src_dir> <out_dir> [--hash <hash>]"""
import gzip
import hashlib
import json
import sys
import tarfile
import tempfile
from base64 import b64encode, urlsafe_b64encode
from pathlib import Path

from compiledtext import encode, decode


def build_bundle(cv: str, src_dir: Path, out_dir: Path, override_hash: str | None = None) -> None:
    files = sorted(src_dir.glob("*.json"))
    if not files:
        sys.exit(f"no *.json files found in {src_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_list = []
    with tempfile.TemporaryDirectory() as work_str:
        work = Path(work_str)
        for path in files:
            plain = path.read_bytes()
            member = encode(plain)
            if decode(member) != plain:
                sys.exit(f"self-check failed encoding {path.name} -- refusing to publish a broken bundle")

            member_b64 = b64encode(member)
            (work / path.name).write_bytes(member_b64)
            manifest_list.append({"Name": path.name, "Hash": hashlib.md5(member_b64).hexdigest()})
            print(f"  encoded {path.name} ({len(plain)} -> {len(member_b64)} bytes)")

        tar_path = work / "bundle.tar"
        with tarfile.open(tar_path, "w", format=tarfile.USTAR_FORMAT) as tar:
            for path in files:
                tar.add(work / path.name, arcname=path.name)
        tar_bytes = tar_path.read_bytes()

    wrapped = urlsafe_b64encode(gzip.compress(tar_bytes)).decode("ascii").replace("=", ",")
    wrapped = urlsafe_b64encode(gzip.compress(wrapped.encode("ascii"))).decode("ascii").replace("=", ",")
    bundle_text = wrapped

    bundle_hash = override_hash if override_hash else hashlib.sha256(bundle_text.encode("ascii")).hexdigest()

    manifest_json = json.dumps({"File": {"List": manifest_list}}, separators=(",", ":"))
    manifest_blob = b64encode(encode(manifest_json.encode("utf-8"))).decode("ascii")
    manifest_blob = manifest_blob.replace("+", "-").replace("/", "_").replace("=", ",")

    (out_dir / f"{bundle_hash}.txt").write_text(bundle_text, encoding="ascii")
    (out_dir / f"{bundle_hash}_md5.txt").write_text(manifest_blob, encoding="ascii")

    print(f"\nbundle hash: {bundle_hash}")
    print(f"wrote: {out_dir / (bundle_hash + '.txt')}")
    print(f"wrote: {out_dir / (bundle_hash + '_md5.txt')}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Pack plaintext level JSON into a level_shipping bundle.")
    ap.add_argument("cv")
    ap.add_argument("src_dir", type=Path)
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--hash", dest="override_hash")
    args = ap.parse_args()
    build_bundle(args.cv, args.src_dir, args.out_dir, args.override_hash)
