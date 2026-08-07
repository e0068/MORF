#!/usr/bin/env python3
"""Holds a commit that skipped review to the Under Observation ledger.

The working practice runs a reviewer and a tester over a change and treats
both verdicts as a gate. A hook cannot see whether they ran, so the agent
records their verdicts and this reads them at `git commit`. Both satisfied,
the commit passes and the record is spent. Otherwise the change must carry an
entry in UNDER-OBSERVATION.md staged in the same commit, or it is blocked:
what ships unreviewed does not ship unwatched.

    gate-observation.py --record <reviewer> <tester>   the agent, after review
    gate-observation.py                                 PreToolUse, on every Bash

Runs on PreToolUse. Exit 2 blocks the call and sends stderr to the agent.
Any breakage fails open — a process gate must never wedge the owner's commit.
No dependencies beyond the standard library, save morf for the state path.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

LEDGER = "UNDER-OBSERVATION.md"
SATISFIED = re.compile(r"satisf", re.I)
# `git commit` as the subcommand, at a command head or after a shell separator,
# tolerating env-var prefixes (`GIT_DIR=x git …`) and any run of leading global
# options (`-c k=v`, `-C dir`, `--no-pager`, `--git-dir=…`). Not `commit-graph`,
# and not a bare `git commit` sitting inside a quoted argument.
COMMIT = re.compile(
    r"(?:&&|\|\||^|[\n;&|(])\s*"
    r"(?:\w+=\S+\s+)*"
    r"git\b(?:\s+-[cC]\s+\S+|\s+--?[\w-]+(?:=\S+)?)*"
    r"\s+commit(?![-\w])",
    re.M,
)


def review_file(cwd: str) -> Path:
    """One record per checkout, keyed by the git root so `--record` from a
    subdirectory still names the commit's file. Falls back to the raw folder."""
    import morf
    try:
        root = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        if root:
            cwd = root
    except (OSError, subprocess.SubprocessError):
        pass
    return morf.state() / f"review-{morf.slot(cwd)}.json"


def record(reviewer: str, tester: str) -> None:
    if not reviewer or not tester:
        print("both a reviewer and a tester verdict are needed; a missing one "
              f"never clears a commit (reviewer={reviewer!r} tester={tester!r})",
              file=sys.stderr)
    path = review_file(os.getcwd())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"reviewer": reviewer, "tester": tester}), encoding="utf-8")
    print(f"recorded: reviewer={reviewer!r} tester={tester!r}")


def both_satisfied(cwd: str) -> bool:
    """True only if a record exists and names both verdicts satisfied."""
    try:
        v = json.loads(review_file(cwd).read_text(encoding="utf-8"))
        return bool(SATISFIED.search(v.get("reviewer", ""))
                    and SATISFIED.search(v.get("tester", "")))
    except (OSError, ValueError, AttributeError):
        return False


def ledger_staged(cwd: str) -> bool:
    """Is an Under Observation entry staged in this very commit?

    Fails open — a git that will not answer must not turn into a block.
    """
    try:
        out = subprocess.run(["git", "-C", cwd, "diff", "--cached", "--name-only"],
                             capture_output=True, text=True, timeout=5, check=True).stdout
        return any(Path(line).name == LEDGER for line in out.splitlines())
    except (OSError, subprocess.SubprocessError):
        return True


def main() -> None:
    if "--record" in sys.argv:
        rest = sys.argv[sys.argv.index("--record") + 1:]
        record(rest[0] if rest else "", rest[1] if len(rest) > 1 else "")
        return

    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    if event.get("tool_name") != "Bash":
        return
    if not COMMIT.search((event.get("tool_input") or {}).get("command", "")):
        return
    cwd = event.get("cwd") or os.getcwd()

    try:
        if both_satisfied(cwd):
            review_file(cwd).unlink(missing_ok=True)   # spent: one record clears one commit
            return
        if ledger_staged(cwd):
            return
    except Exception:      # noqa: BLE001 — a process gate must not wedge a commit on its own bug
        return

    print(
        f"Blocked: this commit cleared neither a recorded reviewer-and-tester pass "
        f"nor an {LEDGER} entry. If both did pass, run `gate-observation.py --record "
        f"<reviewer> <tester>` first; otherwise record an entry (problem, fix, what "
        f"was tried, the dates) and stage {LEDGER} in this commit. A record is spent "
        f"once a commit clears — if a commit failed and you are retrying, record "
        f"again. What ships unreviewed does not ship unwatched.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
