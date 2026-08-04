#!/usr/bin/env python3
"""Builds the installer from the tree this script sits in.

    python3 tools/build-release.py

`Install-MORF.command` is one file: the body from `tools/installer.sh`, then a
base64 tar of the plugin appended after the `__PAYLOAD__` line. The body lives
in the repository rather than only inside the artifact it produces — otherwise
every edit to it survives in one place only, the copy someone downloaded.

The build machinery is left out of the payload: what gets installed is the
plugin, not the means of packing it. Timestamps are zeroed, so the same tree
gives the same bytes.
No dependencies beyond the standard library.
"""

import base64
import io
import sys
import tarfile
import tempfile
from pathlib import Path

# ===== Settings =====

ROOT = Path(__file__).resolve().parent.parent
BODY = ROOT / "tools" / "installer.sh"
TARGET = ROOT / "dist" / "Install-MORF.command"
MARKER = "__PAYLOAD__"
SKIP = {".git", ".DS_Store", "dist", "tools", "__pycache__"}
WIDTH = 100


# ===== The payload =====

def sources() -> list[Path]:
    """Every file that belongs to the plugin, in a stable order."""
    return sorted(p for p in ROOT.rglob("*")
                  if p.is_file() and not SKIP & set(p.relative_to(ROOT).parts))


def pack(files: list[Path]) -> bytes:
    """One tar.gz, without the timestamps that would make two builds differ."""
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w:gz", compresslevel=9, format=tarfile.GNU_FORMAT) as tar:
        tar.mtime = 0
        for path in files:
            info = tar.gettarinfo(path, arcname=f"./{path.relative_to(ROOT).as_posix()}")
            info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, "", ""
            with path.open("rb") as handle:
                tar.addfile(info, handle)
    return raw.getvalue()


# ===== Checking what was built =====

def unpacked(archive: bytes) -> dict[str, bytes]:
    """Path to content, as the installer will see it."""
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            tar.extractall(tmp, filter="data")
        root = Path(tmp)
        return {p.relative_to(root).as_posix(): p.read_bytes()
                for p in sorted(root.rglob("*")) if p.is_file()}


def differences(archive: bytes, files: list[Path]) -> list[str]:
    """What the payload would install that is not what the tree holds."""
    here = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in files}
    there = unpacked(archive)
    return ([f"missing from the payload: {name}" for name in sorted(set(here) - set(there))]
            + [f"in the payload only: {name}" for name in sorted(set(there) - set(here))]
            + [f"differs: {name}" for name in sorted(set(here) & set(there))
               if here[name] != there[name]])


# ===== Entry point =====

def main() -> None:
    body = BODY.read_text(encoding="utf-8")
    if not body.rstrip("\n").endswith(MARKER):
        sys.exit(f"{BODY.name} must end with the {MARKER} line: the payload goes after it.")

    files = sources()
    archive = pack(files)
    broken = differences(archive, files)
    if broken:
        sys.exit("The payload does not match the tree:\n  " + "\n  ".join(broken))

    encoded = base64.b64encode(archive).decode()
    wrapped = "\n".join(encoded[i:i + WIDTH] for i in range(0, len(encoded), WIDTH))
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(body + wrapped + "\n", encoding="utf-8")
    TARGET.chmod(0o755)

    print(f"{TARGET.relative_to(ROOT)} — {TARGET.stat().st_size // 1024} KB, "
          f"{len(files)} files, payload verified against the tree.")
    print("Attach it to the release; nothing else is downloaded.")


if __name__ == "__main__":
    main()
