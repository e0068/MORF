#!/usr/bin/env python3
"""Builds the self-extracting installer from the tree this script sits in.

    python3 tools/build-release.py

MORF is no longer a plugin dropped into `~/.claude`; it is a `.morf/` folder
dropped into a repository. The artifact reflects that: `dist/install-morf.sh` is
one file — the self-extract header from `tools/selfextract.sh`, then a base64
tar of the payload appended after the `__PAYLOAD__` line. Running it unpacks to
a temp dir and runs `install.sh`, so a `.morf` lands in a repo without cloning.

The payload is exactly what `install.sh` consumes: `install.sh` itself at the
root, beside `scripts/`, `hooks/`, `commands/`, `docs/` and the canvas assets —
the build machinery, tests, the vestigial plugin manifest and the docs-only top
level are left out. Timestamps are zeroed, so the same tree gives the same
bytes. No dependencies beyond the standard library.
"""

import base64
import gzip
import io
import sys
import tarfile
import tempfile
from pathlib import Path

# ===== Settings =====

ROOT = Path(__file__).resolve().parent.parent
HEADER = ROOT / "tools" / "selfextract.sh"
INSTALLER = ROOT / "tools" / "install.sh"
TARGET = ROOT / "dist" / "install-morf.sh"
MARKER = "__PAYLOAD__"

# The directories that go into a `.morf/`. `install.sh` copies scripts, hooks,
# commands, docs and the canvases; those plus install.sh are the whole payload.
PAYLOAD_DIRS = ("scripts", "hooks", "commands", "docs")
SKIP = {".git", ".DS_Store", "__pycache__"}
WIDTH = 100


# ===== The payload =====

def sources() -> list[tuple[Path, str]]:
    """(file on disk, arcname in the payload), in a stable order.

    install.sh sits at the payload root; the directories keep their names; the
    canvas assets are flattened to the root, which is where install.sh places
    them inside `.morf/` and where the docs describe them. SKILL.md rides at the
    root too, beside install.sh, which registers it under `.claude/skills/morf/`.
    """
    picked: list[tuple[Path, str]] = [(INSTALLER, "install.sh"), (ROOT / "SKILL.md", "SKILL.md")]
    for sub in PAYLOAD_DIRS:
        base = ROOT / sub
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_file() and not SKIP & set(path.relative_to(ROOT).parts):
                picked.append((path, path.relative_to(ROOT).as_posix()))
    for canvas in sorted((ROOT / "assets").glob("*.canvas")):
        picked.append((canvas, canvas.name))
    return sorted(picked, key=lambda pair: pair[1])


def pack(files: list[tuple[Path, str]]) -> bytes:
    """One tar.gz whose bytes depend on the tree alone, not on the clock.

    The inner tar zeroes every member's mtime; the outer gzip layer is built
    explicitly with `mtime=0` too. `tarfile.open(mode="w:gz")` would otherwise
    stamp the gzip header with the current time, so two builds of the same tree
    would differ. The GzipFile is closed after the tar context exits — closing
    it flushes the trailer, and skipping that truncates the payload.
    """
    raw = io.BytesIO()
    gz = gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0)
    with tarfile.open(fileobj=gz, mode="w:", format=tarfile.GNU_FORMAT) as tar:
        tar.mtime = 0
        for path, arcname in files:
            info = tar.gettarinfo(path, arcname=f"./{arcname}")
            info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, "", ""
            if arcname.endswith(".sh"):
                info.mode = 0o755
            with path.open("rb") as handle:
                tar.addfile(info, handle)
    gz.close()
    return raw.getvalue()


# ===== Checking what was built =====

def unpacked(archive: bytes) -> dict[str, bytes]:
    """Path to content, as install.sh will see it."""
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            tar.extractall(tmp, filter="data")
        root = Path(tmp)
        return {p.relative_to(root).as_posix(): p.read_bytes()
                for p in sorted(root.rglob("*")) if p.is_file()}


def differences(archive: bytes, files: list[tuple[Path, str]]) -> list[str]:
    """What the payload would carry that is not what the tree holds."""
    here = {arcname: path.read_bytes() for path, arcname in files}
    there = unpacked(archive)
    return ([f"missing from the payload: {name}" for name in sorted(set(here) - set(there))]
            + [f"in the payload only: {name}" for name in sorted(set(there) - set(here))]
            + [f"differs: {name}" for name in sorted(set(here) & set(there))
               if here[name] != there[name]])


# ===== Entry point =====

def main() -> None:
    header = HEADER.read_text(encoding="utf-8")
    if not header.rstrip("\n").endswith(MARKER):
        sys.exit(f"{HEADER.name} must end with the {MARKER} line: the payload goes after it.")

    files = sources()
    archive = pack(files)
    broken = differences(archive, files)
    if broken:
        sys.exit("The payload does not match the tree:\n  " + "\n  ".join(broken))

    encoded = base64.b64encode(archive).decode()
    wrapped = "\n".join(encoded[i:i + WIDTH] for i in range(0, len(encoded), WIDTH))
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(header + wrapped + "\n", encoding="utf-8")
    TARGET.chmod(0o755)

    print(f"{TARGET.relative_to(ROOT)} — {TARGET.stat().st_size // 1024} KB, "
          f"{len(files)} files, payload verified against the tree.")
    print("Attach it to the release; run it inside a repo to drop in `.morf`.")


if __name__ == "__main__":
    main()
