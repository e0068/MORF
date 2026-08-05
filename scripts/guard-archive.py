#!/usr/bin/env python3
"""Keeps the agent out of the conversation archive.

The archive is filled by exactly one path: copying from Claude Code's own
history, done by a hook rather than a tool. So any tool call touching
Transcripts is either a mistake or an attempt to erase evidence, and telling
them apart is pointless: there are no legitimate cases.

What is checked differs by tool, and the difference is the whole guard.
A write is judged by where it lands, never by what it says: matching the
whole payload made a note that merely quotes the archive path count as a
write into the archive, and blocked editing the very instructions that name
it. A shell command has no destination to read, so there the payload is all
there is — and the removal it hides may be spelled any number of ways.

Runs on PreToolUse. Exit 2 blocks the call and sends stderr to the agent.
The owner is unaffected: they edit files outside the agent's tools.
No dependencies beyond the standard library.
"""

import json
import re
import sys

# ===== Settings =====

# The tail of the path, not the whole of it: the folder above is wherever its
# owner put it and may be called anything, while these two segments are ours.
# Spelled out rather than imported, because this hook runs on every tool call
# and a guard that fails open on a broken sibling import guards nothing.
GUARDED = "Memory/Transcripts"
WRITERS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
TARGETS = ("file_path", "notebook_path", "path")
SHELL = ("Bash", "BashOutput")

# Every shape a removal or an overwrite takes in a shell: the command word,
# the flag that makes a search delete what it finds, the call a script makes,
# the mode a file is opened in. A literal list of four words let `find
# -delete`, `shutil.rmtree`, `os.remove` and a plain `cp` over a transcript
# straight through. Over-matching on these costs nothing — the pattern is
# consulted only once the archive is already named, and behind that name no
# legitimate write remains.
#
# The redirect is the exception and has to name the archive itself. A bare
# `>` also matches `2>&1` and a listing sent to a file elsewhere, and reads
# are the whole reason this branch weighs the command instead of blocking on
# the name the way writes do.
DESTRUCTIVE = re.compile(
    r"\b(?:rm|rmdir|rmtree|remove|removedirs|mv|move|cp|tee|install|shred"
    r"|unlink|truncate|dd|rename|replace)\b"
    r"|--?delete\b|\bgit\s+clean\b|\bsed\s+-i"
    r"|\bopen\([^)]*['\"][wa]"
    rf"|>\s*\S*{re.escape(GUARDED)}"
)


# ===== Reading the call =====

def mentions_archive(payload: str) -> bool:
    """The archive path in any shape: as an argument, a flag, inside a command."""
    return GUARDED in payload or GUARDED.replace("/", "\\/") in payload


def destination(event: dict) -> str:
    """Where a write lands. The target fields only, never the content."""
    tool_input = event.get("tool_input") or {}
    return " ".join(str(tool_input.get(key, "")) for key in TARGETS)


def verdict(event: dict) -> str:
    """Returns the reason to block, or an empty string."""
    tool = event.get("tool_name", "")
    if tool in WRITERS:
        return "writing into the archive" if mentions_archive(destination(event)) else ""
    if tool in SHELL:
        payload = json.dumps(event.get("tool_input", {}), ensure_ascii=False)
        if mentions_archive(payload) and DESTRUCTIVE.search(payload):
            return "deleting or overwriting inside the archive"
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
