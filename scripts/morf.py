#!/usr/bin/env python3
"""Where MORF is.

The plugin is installed once and runs in any project, so the path cannot be
hardcoded. It comes from an environment variable, or from the pointer the
installer writes. The folder is the memory itself, not a container for it:
nothing above it is ours, and no script looks there.
"""

import json
import os
import subprocess
from pathlib import Path

POINTER = Path.home() / ".claude" / "morf-path"


def home() -> Path:
    """The MORF folder. Order: environment variable, pointer file, home."""
    env = os.environ.get("MORF_HOME")
    if env:
        return Path(env).expanduser()
    if POINTER.is_file():
        return Path(POINTER.read_text(encoding="utf-8").strip()).expanduser()
    return Path.home() / "MORF"


def memory() -> Path:
    return home() / "Memory"


def facts() -> Path:
    return home() / "Facts"


def state() -> Path:
    return memory() / ".state"


def slot(cwd: str) -> str:
    """A file name for the working folder: the only key both the hook and the
    command know, since a command is given no session id."""
    path = Path(cwd).expanduser() if cwd else Path.cwd()
    return str(path).strip("/").replace("/", "-") or "root"


def project(cwd: str) -> str:
    """The project a session feeds — its shelves, its scale, its debt.

    A working folder is a slot, not an identity: a worktree is named after the
    task, not the project it is work on, so its own name shelves nothing.
    Resolved by the relation, not the folder name that stands in for it — the
    order is the judgement the agent recorded at handoff, then a git seed (a
    checkout, and every worktree of it, is named by its main checkout), then
    the folder name for anything ungit. A dash for the vault itself and for
    the home directory: neither is a project.
    """
    path = Path(cwd).expanduser() if cwd else Path.cwd()
    if path in (home(), Path.home()):
        return "—"
    try:
        recorded = json.loads((state() / f"{slot(cwd)}.json")
                              .read_text(encoding="utf-8")).get("project")
        if isinstance(recorded, str) and recorded:
            return recorded
    except (OSError, ValueError, AttributeError):
        pass
    try:
        common = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        if common:
            git_dir = Path(common) if Path(common).is_absolute() else path / common
            return git_dir.resolve().parent.name
    except (OSError, subprocess.SubprocessError):
        pass
    return path.name or "—"
