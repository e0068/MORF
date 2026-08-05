#!/usr/bin/env python3
"""Extracts a readable conversation from an archived transcript.

    python3 read-session.py 260803-a41f              whole conversation
    python3 read-session.py 260803-a41f#412-980      one stretch only
    python3 read-session.py 260803-a41f cache        around a word only

Reads every file of the session, subagents included. Reasoning is shown:
that is usually where the answer to «why did we decide that» lives.
Tool calls and their output are skipped — that is machinery, not thought.

A subagent is written to its own file, so the line numbers of a stretch say
nothing about it: asking for one stretch used to return the main transcript
alone, and the reasoning the command promises lives mostly in the agents.
Time places them instead — the stretch fixes a window in the main transcript,
and a subagent turn belongs to it when it falls inside. Everything is merged
into one timeline, so the agents speak where they actually spoke.
No dependencies beyond the standard library.
"""

import json
import sys
from pathlib import Path

import morf

# ===== Settings =====

TRANSCRIPTS = morf.memory() / "Transcripts"
CONTEXT_LINES = 2
MAX_CHARS = 600

Turn = tuple[str, str, str, str]   # stamp, role, speaker, text


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


def read_turns(path: Path, speaker: str = "", span: str = "") -> list[Turn]:
    """Stamp, role, speaker and text of every turn in one file, in file order.

    A turn without a timestamp of its own inherits the previous one, so it
    stays beside its neighbours instead of sinking to the start of the merge.
    """
    found, clock = [], ""
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not in_span(index, span):
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        clock = entry.get("timestamp") or clock
        role = (entry.get("message") or {}).get("role", "")
        text = extract_text(entry).strip()
        if role in ("user", "assistant") and text:
            found.append((clock, role, speaker, text))
    return found


# ===== Placing the subagents =====

def speaker_of(path: Path) -> str:
    """A subagent is named by the role it was spawned as, from its meta file."""
    try:
        meta = json.loads(path.with_suffix(".meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "subagent"
    return meta.get("agentType") or "subagent"


def window(paths: list[Path], span: str) -> tuple[str, str]:
    """The stretch of time the span covers, taken from every line it holds.

    Not from the turns kept above. A subagent runs between the turn that
    spawned it and the tool result that follows, and a result line carries no
    text of its own, so a window built from turns alone closed before the
    agent had answered: a stretch ending where the piece of work ended —
    which is where `--handoff` always ends it — dropped exactly the reasoning
    it was opened for.
    """
    found = []
    for path in paths:
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not in_span(index, span):
                continue
            try:
                stamp = json.loads(line).get("timestamp")
            except json.JSONDecodeError:
                continue
            if stamp:
                found.append(stamp)
    return (min(found), max(found)) if found else ("", "")


def within(stamp: str, first: str, last: str) -> bool:
    """No window to place an agent against — a session archived without its
    main transcript, or a span that matched no line — so it belongs."""
    return not first or first <= stamp <= last


def collect(session: list[Path], nested: list[Path], span: str) -> list[Turn]:
    """One timeline out of the session and its agents."""
    turns = [turn for path in session for turn in read_turns(path, span=span)]
    first, last = window(session, span)
    for path in nested:
        turns += [turn for turn in read_turns(path, speaker_of(path))
                  if within(turn[0], first, last)]
    return sorted(turns, key=lambda turn: turn[0])


# ===== Selecting and rendering =====

def select(turns: list[Turn], needle: str) -> list[tuple[int, Turn]]:
    """Without a word: the whole conversation. With one: matches and neighbours."""
    if not needle:
        return list(enumerate(turns))
    hits = [i for i, (*_, text) in enumerate(turns) if needle.lower() in text.lower()]
    keep = sorted({j for i in hits for j in range(i - CONTEXT_LINES, i + CONTEXT_LINES + 1)})
    return [(i, turns[i]) for i in keep if 0 <= i < len(turns)]


def label(role: str, speaker: str) -> str:
    """Who is speaking. Inside a subagent the owner is not present at all:
    a `user` turn there is what the agent above handed down."""
    if not speaker:
        return "You" if role == "user" else "Claude"
    return f"{speaker} ← task" if role == "user" else speaker


def render(selected: list[tuple[int, Turn]]) -> str:
    out, previous = [], None
    for index, (_, role, speaker, text) in selected:
        if previous is not None and index != previous + 1:
            out.append("\n…\n")
        body = text if len(text) <= MAX_CHARS else text[:MAX_CHARS] + " […]"
        out.append(f"**{label(role, speaker)}:** {body}\n")
        previous = index
    return "\n".join(out) if out else "No matches."


# ===== Entry point =====

def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Give a session id, for example 260803-a41f")
    slug, _, span = sys.argv[1].removeprefix("s:").partition("#")
    needle = " ".join(sys.argv[2:])

    folder = TRANSCRIPTS / slug
    files = sorted(folder.rglob("*.jsonl")) if folder.is_dir() else []
    session = [path for path in files if path.parent == folder]
    nested = [path for path in files if path.parent != folder]
    if not files:
        legacy = TRANSCRIPTS / f"{slug}.jsonl"
        session = [legacy] if legacy.is_file() else []
    if not session and not nested:
        sys.exit(f"No {slug} in the archive: the session was cut short before its stretch was copied.")

    print(render(select(collect(session, nested, span), needle)))


if __name__ == "__main__":
    main()
