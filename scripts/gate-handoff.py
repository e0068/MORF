#!/usr/bin/env python3
"""Refuses work while a stretch is waiting to be turned into observations.

The session start can report an unprocessed stretch but cannot stop anything:
by the time it runs the session already exists, and its message competes with
whatever the owner just asked for. A message loses that competition every
time, which is how a folder of transcripts grows next to empty levels.

So the refusal lives here. Runs on UserPromptSubmit, the one event that can
actually block: exit 2 discards the prompt and sends stderr to the agent.
The prompt is echoed back in the message, because a gate that eats what you
typed teaches you to hate it.

Anything mentioning the handoff passes, or there would be no way out. So does
deleting the pending file by hand — the owner works outside the tools.
Any breakage fails open: a guard nobody can bypass is worse than no guard.
No dependencies beyond the standard library.
"""

import json
import sys
from pathlib import Path

import morf

# ===== Settings =====

STATE = morf.memory() / ".state"

# The way out has to survive the block that prompted it.
PASSES = ("handoff", "/morf", "morf:", "консолид")


# ===== Decision =====

def pending_of(cwd: str) -> Path:
    """The state is keyed by the working folder — see archive-session.py."""
    path = Path(cwd).expanduser() if cwd else Path.cwd()
    return STATE / f"{str(path).strip('/').replace('/', '-') or 'root'}.pending"


def prompt_of(event: dict) -> str:
    return str(event.get("prompt", ""))


def lets_through(prompt: str) -> bool:
    """A prompt that is itself the remedy, or asks about it."""
    low = prompt.lower()
    return any(word in low for word in PASSES)


# ===== Entry =====

def main() -> None:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return                      # cannot read the prompt, do not block it

    try:
        ref = pending_of(event.get("cwd", "")).read_text(encoding="utf-8").strip()
    except OSError:
        return                      # nothing pending here, or nothing readable
    if not ref:
        return

    prompt = prompt_of(event)
    if lets_through(prompt):
        return

    print(
        f"MORF: the stretch {ref} is archived but never turned into observations, "
        f"and levels stay empty while that is true.\n"
        f"Run /handoff for it, then send this again:\n\n{prompt}",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception:               # a broken gate must never brick a session
        pass
