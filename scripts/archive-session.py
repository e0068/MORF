#!/usr/bin/env python3
"""Maintains the session index and archives transcripts.

SessionStart — adds a row to sessions.md and remembers the session state so
               that /handoff can copy without a hook. It also sweeps in
               transcripts left behind by a cut-short session and tells the
               agent which stretch of the previous one is unprocessed.
--handoff    — copies the transcript now and prints a reference to the
               stretch written since the previous call: s:260803-a41f#412-980.

One hook is enough. Copying is done by /handoff, sweeping by the session
start, and the state is overwritten on the next run: an unclosed tail is
honestly reported as unprocessed.

Nothing is interpreted — only facts that can be established mechanically.
No dependencies beyond the standard library.
"""

import json
import shutil
import sys
from datetime import date
from pathlib import Path

import morf

# ===== Settings =====

HOME = morf.home()
MEMORY = morf.memory()
TRANSCRIPTS = MEMORY / "Transcripts"
SESSIONS = MEMORY / "sessions.md"
STATE = MEMORY / ".state"
HEADER = "| id | date | project | about |\n|---|---|---|---|\n"
CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"


# ===== Reading the event =====

def read_event() -> dict:
    """The hook event arrives on stdin; on any breakage return an empty dict."""
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def session_slug(session_id: str, day: date) -> str:
    """Short identifier such as 260803-a41f."""
    return f"{day:%y%m%d}-{session_id[:4] or 'xxxx'}"


def project_key(cwd: str) -> str:
    """A file name for the working folder, so state is not shared between them.

    One state file for every project made whichever session started last the
    owner of `/handoff`: it answered with another project's slug, then with a
    transcript that no longer existed. The command knows no session id, only
    the folder it runs in — so the folder is what the state is keyed by.
    Two sessions in the *same* folder still share a slot; that one is open.
    """
    path = Path(cwd).expanduser() if cwd else Path.cwd()
    return str(path).strip("/").replace("/", "-") or "root"


def current_of(cwd: str) -> Path:
    return STATE / f"{project_key(cwd)}.json"


def pending_of(cwd: str) -> Path:
    return STATE / f"{project_key(cwd)}.pending"


def project_name(cwd: str) -> str:
    """Project name from the working folder; a dash for MORF itself."""
    path = Path(cwd) if cwd else Path.cwd()
    return "—" if path == HOME else path.name


# ===== Actions =====

def copy_transcripts(source: str, slug: str) -> int:
    """Copies the session transcript and the subagent files belonging to it.

    Claude Code keeps a session's subagent transcripts in a folder named
    after the session, next to the transcript itself. The `.jsonl` files
    lying beside it are other sessions' transcripts, not this one's
    children: picking siblings by modification time gathered peers, stored
    every session twice, and never copied a subagent at all.
    """
    if not source:
        return 0
    origin = Path(source).expanduser()
    if not origin.is_file():
        return 0

    target = TRANSCRIPTS / slug
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origin, target / origin.name)
    copied = 1

    nested = origin.with_suffix("")
    for path in sorted(nested.rglob("*")) if nested.is_dir() else []:
        if not path.is_file():
            continue
        destination = target / path.relative_to(nested)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        copied += 1
    return copied


def append_row(slug: str, day: date, project: str) -> None:
    """Appends a row to the index; a repeated run duplicates nothing."""
    SESSIONS.parent.mkdir(parents=True, exist_ok=True)
    if not SESSIONS.exists():
        SESSIONS.write_text(HEADER, encoding="utf-8")
    if f"| s:{slug} |" in SESSIONS.read_text(encoding="utf-8"):
        return
    with SESSIONS.open("a", encoding="utf-8") as handle:
        handle.write(f"| s:{slug} | {day:%Y-%m-%d} | {project} |  |\n")


# ===== Session state =====

def remember(slug: str, transcript: str, cwd: str) -> None:
    """The hook knows the transcript path, the command does not. Remember it."""
    current = current_of(cwd)
    current.parent.mkdir(parents=True, exist_ok=True)
    current.write_text(json.dumps({"slug": slug, "transcript": transcript, "mark": 0}),
                       encoding="utf-8")


def unfinished(slug: str, cwd: str) -> str:
    """Checks whether the previous session was cut short and finishes its copy.

    The previous state always stays on disk; what matters is whether its tail
    was processed. The copy is finished here, but turning the stretch into
    observations is the agent's job — it cannot be done mechanically.
    Returns a message for the agent: SessionStart stdout reaches the context.
    """
    try:
        state = json.loads(current_of(cwd).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    if state.get("slug") == slug:
        return ""   # the same session resumed, nothing was cut short

    origin = Path(state.get("transcript", "")).expanduser()
    if not origin.is_file():
        return f"Previous session {state.get('slug')} was cut short; its transcript is missing."

    copy_transcripts(str(origin), state["slug"])
    lines = sum(1 for _ in origin.open(encoding="utf-8", errors="ignore"))
    start = state.get("mark", 0) + 1
    if start > lines:
        return ""   # everything processed, only an empty tail was cut
    ref = f"s:{state['slug']}#{start}-{lines}"
    pending_of(cwd).write_text(ref, encoding="utf-8")
    return (f"The previous session was cut short before /handoff. Its transcript "
            f"has been swept in; the stretch {ref} is unprocessed — run /handoff "
            f"for it before taking on anything new.")


def handoff() -> str:
    """Copies the transcript and returns a reference to the latest stretch.

    The copy ends exactly where the piece of work ended, so the number of the
    last line is the mark: the range between two calls defines the stretch
    without a single guess.
    """
    current = current_of("")
    try:
        state = json.loads(current.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "this folder has no registered session: SessionStart did not run here"

    origin = Path(state["transcript"]).expanduser()
    if not origin.is_file():
        return f"transcript not found: {origin}"

    copy_transcripts(state["transcript"], state["slug"])
    lines = sum(1 for _ in origin.open(encoding="utf-8", errors="ignore"))
    start, state["mark"] = state["mark"] + 1, lines
    current.write_text(json.dumps(state), encoding="utf-8")
    pending_of("").unlink(missing_ok=True)
    return f"s:{state['slug']}#{start}-{lines}"


# ===== Sweeping =====

def sweep() -> int:
    """Copies transcripts that have no folder in the archive yet.

    A hard stop leaves no chance to copy: window closed, process killed,
    machine shut down. The conversation itself is intact — Claude Code writes
    it as the session goes — so the loss is repaired by copying.
    """
    if not CLAUDE_PROJECTS.is_dir():
        return 0
    TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    known = {folder.name.split("-")[-1] for folder in TRANSCRIPTS.iterdir() if folder.is_dir()}

    recovered = 0
    for path in CLAUDE_PROJECTS.glob("*/*.jsonl"):
        tail = path.stem[:4]
        if not tail or tail in known:
            continue
        day = date.fromtimestamp(path.stat().st_mtime)
        target = TRANSCRIPTS / f"{day:%y%m%d}-{tail}"
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target / path.name)
        known.add(tail)
        recovered += 1
    return recovered


# ===== Entry point =====

def main() -> None:
    if "--handoff" in sys.argv:
        print(handoff())
        return

    event = read_event()
    today = date.today()
    slug = session_slug(event.get("session_id", ""), today)

    cwd = event.get("cwd", "")
    message = unfinished(slug, cwd)
    append_row(slug, today, project_name(cwd))
    remember(slug, event.get("transcript_path", ""), cwd)
    sweep()
    if message:
        print(message)


if __name__ == "__main__":
    main()
