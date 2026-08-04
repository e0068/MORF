#!/usr/bin/env python3
"""Keeps the agent out of the conversation archive.

The archive is filled by exactly one path: copying from Claude Code's own
history, done by a hook rather than a tool. So any tool call touching
Transcripts is either a mistake or an attempt to erase evidence, and telling
them apart is pointless: there are no legitimate cases.

Runs on PreToolUse. Exit 2 blocks the call and sends stderr to the agent.
The owner is unaffected: they edit files outside the agent's tools.
No dependencies beyond the standard library.
"""

import json
import sys

# ===== Settings =====

# The tail of the path, not the whole of it: the folder above is wherever its
# owner put it and may be called anything, while these two segments are ours.
# Spelled out rather than imported, because this hook runs on every tool call
# and a guard that fails open on a broken sibling import guards nothing.
GUARDED = "Memory/Transcripts"
WRITERS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
SHELL = ("Bash", "BashOutput")
DESTRUCTIVE = ("rm ", "rm\t", "mv ", "truncate", "> ", "shred", "unlink")


# ===== Reading the call =====

def mentions_archive(payload: str) -> bool:
    """The archive path in any shape: as an argument, a flag, inside a command."""
    return GUARDED in payload or GUARDED.replace("/", "\\/") in payload


def verdict(event: dict) -> str:
    """Returns the reason to block, or an empty string."""
    tool = event.get("tool_name", "")
    payload = json.dumps(event.get("tool_input", {}), ensure_ascii=False)
    if not mentions_archive(payload):
        return ""

    if tool in WRITERS:
        return "writing into the archive"
    if tool in SHELL and any(word in payload for word in DESTRUCTIVE):
        return "deleting or moving inside the archive"
    return ""


# ===== Entry point =====

def main() -> None:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    reason = verdict(event)
    if not reason:
        return

    print(
        f"Blocked: {reason}. The conversation archive is filled only by copying "
        f"from Claude Code's own history and is never edited. If a change is truly "
        f"needed, say so and I will make it myself.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
