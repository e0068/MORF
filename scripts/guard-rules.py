#!/usr/bin/env python3
"""Keeps the agent from editing over someone else's change.

The debt catches drift, but not the worst case:
    the rules were changed outside MORF;
    the agent adds to the same file;
    the edits mix, and telling whose is whose becomes impossible afterwards.
So the diff is needed exactly at the moment the agent is about to write.

Foreign means whatever was already drifted when the session began, which
`archive-session.py` records at `SessionStart`. Without that line the agent
would block itself:
    it writes a rule;
    the file diverges from the snapshot;
    its next edit is refused by a diff of its own work.

Exactly one move is closed — writing over an unaccounted foreign change — and
it opens with a log entry, which is the action the folder exists for.

A broken import opens the way through, on purpose:
    this hook guards the accounting, not the evidence;
    dropping the owner's work over a bookkeeping fault costs more than it saves;
    and the fault is not silent — `due.py` reports it as
    `rules: bookkeeping unreadable` on every turn.
Do not "fix" this to fail closed: it would lock the agent out of the files its
own layer lives in, over a breakage that is already being announced.

Runs on PreToolUse. Exit 2 blocks the call and sends stderr to the agent.
No dependencies beyond the standard library.
"""

import json
import sys
from pathlib import Path

WRITERS = ("Write", "Edit", "MultiEdit", "NotebookEdit")


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    if event.get("tool_name") not in WRITERS:
        return
    target = (event.get("tool_input") or {}).get("file_path")
    if not target:
        return

    sys.path.insert(0, str(Path(__file__).parent))
    try:
        import rules
    except Exception:                      # noqa: BLE001 — see the docstring
        return

    cwd = event.get("cwd") or str(Path.cwd())
    try:
        path = Path(target).expanduser().resolve()
        if str(path) not in rules.foreign(cwd):
            return
        gone, _, _ = rules.unaccounted(path, Path(cwd))
    except Exception:                      # noqa: BLE001
        return
    if not gone:
        return

    lines = "\n".join(f"  − {rule}" for rule in gone)
    print(f"Blocked: {path.name} changed outside MORF and {len(gone)} rule(s) are "
          f"unaccounted.\n{lines}\n"
          f"Write them into the log, run rules.py --seal {path}, then repeat the edit. "
          f"If the seal cannot run, ask the owner to allow it — repeating the edit "
          f"will hit the same wall.",
          file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
