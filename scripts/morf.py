#!/usr/bin/env python3
"""Where MORF is.

The plugin is installed once and runs in any project, so the path cannot be
hardcoded. It comes from an environment variable, or from the pointer the
installer writes. The folder is the memory itself, not a container for it:
nothing above it is ours, and no script looks there.
"""

import os
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
