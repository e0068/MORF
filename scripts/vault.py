#!/usr/bin/env python3
"""Where the vault lives.

The plugin is installed once and runs in any project, so the path cannot be
hardcoded. It comes from an environment variable, or from the pointer the
installer writes.
"""

import os
from pathlib import Path

POINTER = Path.home() / ".claude" / "memory-vault"
FOLDER = "MORF"     # the one folder we own inside the chosen vault; named once, here


def root() -> Path:
    """Vault root. Order: environment variable, pointer file, home."""
    env = os.environ.get("CLAUDE_MEMORY_VAULT")
    if env:
        return Path(env).expanduser()
    if POINTER.is_file():
        return Path(POINTER.read_text(encoding="utf-8").strip()).expanduser()
    return Path.home() / "Vault"


def memory() -> Path:
    return root() / FOLDER / "Memory"
