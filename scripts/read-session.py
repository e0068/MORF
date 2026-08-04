#!/usr/bin/env python3
"""Extracts a readable conversation from an archived transcript.

    python3 read-session.py 260803-a41f              whole conversation
    python3 read-session.py 260803-a41f#412-980      one stretch only
    python3 read-session.py 260803-a41f cache        around a word only

Reads every file of the session, subagents included. Reasoning is shown:
that is usually where the answer to «why did we decide that» lives.
Tool calls and their output are skipped — that is machinery, not thought.
No dependencies beyond the standard library.
"""

import json
import sys
from pathlib import Path

import vault

# ===== Settings =====

TRANSCRIPTS = vault.memory() / "Transcripts"
CONTEXT_LINES = 2
MAX_CHARS = 600


# ===== Reading the transcript =====

def extract_text(entry: dict) -> str:
    """Collects text and reasoning of a turn, ignoring tool calls."""
    message = entry.get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
        elif block.get("type") == "thinking":
            parts.append("〈thinking〉 " + block.get("thinking", ""))
    return "\n".join(p for p in parts if p)


def in_span(index: int, span: str) -> bool:
    """A line range such as 412-980; empty means the whole file."""
    if not span:
        return True
    first, _, last = span.partition("-")
    return int(first) <= index <= int(last or first)


def read_turns(paths: list[Path], span: str = "") -> list[tuple[str, str]]:
    """Returns role-to-text pairs in conversation order across all files."""
    turns = []
    numbered = ((i, l) for p in paths for i, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1))
    for index, line in numbered:
        if not in_span(index, span):
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        role = (entry.get("message") or {}).get("role", "")
        text = extract_text(entry).strip()
        if role in ("user", "assistant") and text:
            turns.append((role, text))
    return turns


# ===== Selecting and rendering =====

def select(turns: list, needle: str) -> list:
    """Without a word: the whole conversation. With one: matches and neighbours."""
    if not needle:
        return list(enumerate(turns))
    hits = [i for i, (_, text) in enumerate(turns) if needle.lower() in text.lower()]
    keep = sorted({j for i in hits for j in range(i - CONTEXT_LINES, i + CONTEXT_LINES + 1)})
    return [(i, turns[i]) for i in keep if 0 <= i < len(turns)]


def render(selected: list) -> str:
    out, previous = [], None
    for index, (role, text) in selected:
        if previous is not None and index != previous + 1:
            out.append("\n…\n")
        body = text if len(text) <= MAX_CHARS else text[:MAX_CHARS] + " […]"
        out.append(f"**{'You' if role == 'user' else 'Claude'}:** {body}\n")
        previous = index
    return "\n".join(out) if out else "No matches."


# ===== Entry point =====

def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Give a session id, for example 260803-a41f")
    slug, _, span = sys.argv[1].removeprefix("s:").partition("#")
    needle = " ".join(sys.argv[2:])

    folder = TRANSCRIPTS / slug
    paths = sorted(folder.glob("*.jsonl")) if folder.is_dir() else []
    if not paths:
        legacy = TRANSCRIPTS / f"{slug}.jsonl"
        paths = [legacy] if legacy.is_file() else []
    if not paths:
        sys.exit(f"No {slug} in the archive: the session was cut short before its stretch was copied.")

    print(render(select(read_turns(paths, span), needle)))


if __name__ == "__main__":
    main()
