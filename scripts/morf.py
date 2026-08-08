#!/usr/bin/env python3
"""Where MORF is.

MORF is a `.morf/` folder dropped inside a repository: the scripts and the
memory they tend live together, so there is nothing to install and nothing to
point at. The running script sits in `.morf/scripts/`, so the home is simply
its own `.morf` — its parent's parent — and the fragile central-install
resolver it replaced is gone.

Two escapes remain, for a script not run from inside a `.morf`. A git worktree
checks out the code but shares one `.morf` with the main checkout; its memory
is that one, found through the common git dir. And for loose, non-git use the
old order survives as a last resort: the environment variable, the pointer
file, then `~/MORF`.
"""

import os
import subprocess
from functools import lru_cache
from pathlib import Path

POINTER = Path.home() / ".claude" / "morf-path"


def _main_checkout_morf(script_home: Path) -> Path | None:
    """The main checkout's `.morf`, when the script runs from a worktree's.

    A worktree is one repository with the main checkout, so `git-common-dir`
    names the shared `.git`; its parent is the main working tree, and the
    `.morf` beside it is the single memory every worktree feeds. Run from the
    main checkout it resolves back to `script_home` itself, so the call is
    idempotent and needs no "am I a worktree" test. `None` when there is no
    git, or no `.morf` there — the caller then keeps its own.
    """
    try:
        common = subprocess.run(
            ["git", "-C", str(script_home), "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, timeout=5, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    if not common:
        return None
    git_dir = Path(common) if Path(common).is_absolute() else script_home / common
    candidate = git_dir.resolve().parent / ".morf"
    return candidate if candidate.is_dir() else None


@lru_cache(maxsize=None)
def home() -> Path:
    """The `.morf` folder this script lives in — code and data together.

    Cached: it is read into a dozen module-level constants and depends only on
    the script's own location and the environment, both fixed for the run, so
    the one git call the worktree case makes happens at most once.
    """
    script_home = Path(__file__).resolve().parent.parent
    if script_home.name == ".morf":
        return _main_checkout_morf(script_home) or script_home
    env = os.environ.get("MORF_HOME")
    if env:
        return Path(env).expanduser()
    if POINTER.is_file():
        return Path(POINTER.read_text(encoding="utf-8").strip()).expanduser()
    return Path.home() / "MORF"


def observations() -> Path:
    """The observation layer: L0..L3 live here, dropped.md sits at the root."""
    return home() / "Observations"


def facts() -> Path:
    return home() / "Facts"


def state() -> Path:
    return home() / ".state"


def slot(cwd: str) -> str:
    """A file name for the working folder: the only key both the hook and the
    command know, since a command is given no session id."""
    path = Path(cwd).expanduser() if cwd else Path.cwd()
    return str(path).strip("/").replace("/", "-") or "root"


def project() -> str:
    """The one project this `.morf` serves: the repository it lives in.

    Memory is no longer sharded by project — one `.morf` is one repo is one
    memory — so nothing composes a `<project>` path segment any more. This name
    only labels the `sessions.md` column and reads back in `/why`; every row is
    the same repo. The old resolver (recorded judgement, git seed, folder-name
    fallback) is gone with the segment it fed: the repo is the checkout that
    holds the `.morf`, so its name is the home's parent's.
    """
    return home().parent.name or "—"
