#!/usr/bin/env python3
"""Maintains the session index and archives transcripts.

SessionStart — adds a row to sessions.md and registers the session in the
               folder's index so that /handoff can copy without a hook. It
               also sweeps in transcripts left behind by sessions that ended
               without one, and tells the agent which stretches are unread.
SessionEnd   — records that a session is over, so that nothing still running
               is swept as though it had been cut short.
--handoff    — copies the transcript now and prints a reference to the
               stretch written since the previous call: s:260803-a41f#412-980.

Every session that registered in a folder is kept there, each with its own
mark: the folder is the only key /handoff is given, but it is not an identity.
A tail nobody handed off stays on the record and is honestly reported as
unprocessed until it is read.

Nothing is interpreted — only facts that can be established mechanically.
No dependencies beyond the standard library.
"""

import json
import os
import shutil
import sys
import time
from datetime import date
from pathlib import Path

import due
import morf

# ===== Settings =====

OBSERVATIONS = morf.observations()
DROPPED = morf.home() / "dropped.md"
TRANSCRIPTS = morf.home() / "Transcripts"
SESSIONS = morf.home() / "sessions.md"
STATE = morf.state()
CONFIG_FILE = Path(__file__).with_name("config.json")
DEFAULT_LEVELS = ["L0", "L1", "L2", "L3"]
HEADER = "| id | date | project | about |\n|---|---|---|---|\n"
CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"

# How long a transcript must stay untouched before the session behind it counts
# as over. Claude Code appends to it on every turn, so silence this long is not
# a session thinking. It only decides the case `SessionEnd` never sees — window
# closed, process killed — and being late here costs a delayed sweep, while
# being early costs a running session reported as cut short.
IDLE = 2 * 3600


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
    the folder it runs in — so the folder is what the *file* is named by. What
    it holds is an index of sessions, not one record.
    """
    return morf.slot(cwd)


def current_of(cwd: str) -> Path:
    return STATE / f"{project_key(cwd)}.json"


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


# ===== Shelves =====

def levels() -> list[str]:
    """Level names, from the same config score-memory.py reads."""
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))["levels"]
    except (OSError, ValueError, KeyError):
        return DEFAULT_LEVELS


def crowding() -> str:
    """Says whether the inbox is owed a consolidation, and how badly.

    The cadence is written in levels.md and nothing ever checked it, so the
    levels that are actually read stayed empty while L0 filled: an empty
    upper level looks like a correct state, not a starved one. Past the
    limit the loss becomes real — further lines displace earlier ones — so
    that is where the notice stops being a notice.
    """
    inbox = OBSERVATIONS / f"{levels()[0]}.md"
    try:
        held = sum(1 for line in inbox.read_text(encoding="utf-8").splitlines()
                   if line.startswith("- "))
    except OSError:
        return ""
    if not held:
        return ""
    limit = limits()[0]
    if held >= limit:
        return (f"the inbox holds {held} lines against a limit of {limit}. "
                f"Further observations displace earlier ones. Consolidate before working.")
    return (f"{held} of {limit} lines in the inbox, none consolidated. "
            f"The levels that are read stay empty until they are filled from it.")


def limits() -> list[int]:
    """Line limits per level, from the same config."""
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))["limits"]
    except (OSError, ValueError, KeyError):
        return [40, 30, 25, 20]


def prepare() -> int:
    """Creates the memory's level files the first time the `.morf` is seen.

    Nothing created them before: /handoff wrote an observation into L0 while
    the levels above it — the ones that are read — did not exist, so the line
    had nowhere to be promoted to and the gap showed only later. The levels
    live in `Observations/`, `dropped.md` at the root; existing files are never
    touched.
    """
    project = morf.project()
    made = 0
    for stem, path in ([(level, OBSERVATIONS / f"{level}.md") for level in levels()]
                       + [("dropped", DROPPED)]):
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nname: {project}-{stem}\n---\n\n", encoding="utf-8")
        made += 1
    return made


# ===== Session state =====
#
# `.state/<working folder>.json` holds `sessions`: one record per session that
# registered in that folder, each with its own transcript, mark and unread
# stretch. A single record per folder meant "the previous session" was
# whichever one last touched it — /handoff answered another session's
# reference, and a session still running in another window was reported as cut
# short. The slug, transcript and mark of the session touched last are also
# written at the top level: `rules.py` reads the slug from there, and an older
# installed copy of this script reads all three.


def load(cwd: str) -> dict:
    """The folder's index. A file written before it existed reads as one entry."""
    try:
        state = json.loads(current_of(cwd).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    if not isinstance(state, dict):
        state = {}
    if not isinstance(state.get("sessions"), dict):
        slug = state.get("slug")
        state["sessions"] = {slug: {"transcript": state.get("transcript", ""),
                                    "mark": state.get("mark", 0)}} if slug else {}
    return state


def save(cwd: str, state: dict, current: str = "") -> None:
    """Writes the index, naming at the top level the session touched last.

    Written aside and moved into place. One file now holds every session of
    the folder, so a truncating write killed halfway would take all their
    marks at once — a mark lost to bookkeeping is the failure this whole
    change exists to end, and it must not come back through the door. The
    staged name carries the process id, because two windows in one folder is
    the ordinary case here: the worst two saves in the same instant can do is
    lose one of them, not publish a file that is half of each.
    """
    if current:
        record = state["sessions"].get(current, {})
        state.update(slug=current, transcript=record.get("transcript", ""),
                     mark=record.get("mark", 0))
    path = current_of(cwd)
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name(f"{path.name}.{os.getpid()}.writing")
    try:
        staged.write_text(json.dumps(state), encoding="utf-8")
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def slug_for(sessions: dict, session_id: str) -> str:
    """The slug this session already registered under, whatever day that was.

    A session resumed after midnight is given a new slug by `session_slug()`,
    and a new slug is a new session: a mark starting at zero and a second row
    in the index for one conversation. The four characters of the id identify
    it; the date only makes the name readable.
    """
    tail = (session_id or "")[:4]
    return next((slug for slug in sessions if tail and slug.endswith(f"-{tail}")), "")


def ended(record: dict) -> bool:
    """Whether the session behind this record is over.

    `SessionEnd` says so outright, but the case worth sweeping is the one that
    hook never sees: window closed, process killed, machine shut down. So a
    transcript untouched for `IDLE` counts as over too, and a transcript that
    is gone counts as over because nothing can still be writing to it.
    """
    if record.get("ended") or not record.get("transcript"):
        return True
    try:
        return time.time() - Path(record["transcript"]).expanduser().stat().st_mtime >= IDLE
    except OSError:
        return True


def prune(sessions: dict, keep: str) -> None:
    """Forgets sessions Claude Code no longer keeps and that owe nothing.

    The index would otherwise grow for the life of the folder. A record is
    dropped only when its transcript is gone *and* nothing unread stands
    against it: a debt outlives the file it was raised from. The session
    registering right now is kept whatever the hook told us about its file.
    """
    for slug in [name for name, record in sessions.items()
                 if name != keep and not record.get("pending")
                 and not Path(record.get("transcript") or "").expanduser().is_file()]:
        del sessions[slug]


def remember(slug: str, transcript: str, cwd: str) -> None:
    """Registers the session in the folder's index, keeping what it earned.

    This ran on every start, resume and compact and wrote the mark back to
    zero each time — into the very field `/handoff` uses to record the last
    line it handed off. A session that came back after a handoff was therefore
    reported at its next start as unread from line 1, and hours of it, already
    written into the memory as observations, were read a second time. Only a
    session this folder has not seen before starts at zero.
    """
    state = load(cwd)
    record = state["sessions"].setdefault(slug, {"mark": 0})
    record["transcript"] = transcript or record.get("transcript", "")
    record["ended"] = False
    prune(state["sessions"], keep=slug)
    save(cwd, state, slug)


def settled(record: dict, covered: dict) -> bool:
    """Whether the memory now accounts for this record's unread stretch.

    A stretch written up names itself as its source, so the memory says when
    a debt is paid. Nothing else did: the marker survived the work it stood
    for, and a session kept its record — and its line at every session start
    — for as long as the folder lived.
    """
    return not due.unread(record["pending"], covered)


def unfinished(slug: str, cwd: str) -> str:
    """Finishes the copy for sessions of this folder that ended unprocessed.

    A mismatched slug used to be proof enough that the previous session was
    cut short. It was not: it also matched a session working in another window
    at that moment. Only a session that has actually ended is swept, and each
    keeps its own unread stretch instead of overwriting the one before it.

    The copy is finished here; turning a stretch into observations is the
    agent's job. Returns a message for it: SessionStart stdout reaches the
    context.
    """
    state, notes, covered, changed = load(cwd), [], None, False
    for other, record in state["sessions"].items():
        if other == slug or not ended(record):
            continue
        if record.get("pending"):
            covered = due.read_up_to() if covered is None else covered
            if settled(record, covered):
                del record["pending"]
                changed = True
        if not (origin := Path(record.get("transcript") or "").expanduser()).is_file():
            continue    # gone from Claude Code's store; the archived copy remains
        stamp = [origin.stat().st_mtime, origin.stat().st_size]
        if record.get("swept") == stamp:
            continue    # not a line has been written to it since we last looked
        copy_transcripts(str(origin), other)
        lines = sum(1 for _ in origin.open(encoding="utf-8", errors="ignore"))
        record["swept"], changed = stamp, True
        start = record.get("mark", 0) + 1
        if start > lines:
            continue    # everything processed, only an empty tail was cut
        record["pending"] = ref = f"s:{other}#{start}-{lines}"
        notes.append(f"The session {other} ended before /handoff. Its transcript "
                     f"has been swept in; the stretch {ref} is unprocessed — run "
                     f"/handoff for it before taking on anything new.")
    if changed:
        save(cwd, state)
    return "\n".join(notes)


def caller(state: dict) -> str:
    """Which session is running `/handoff`.

    The command is given no session id, and answering with whichever session
    registered in the folder last handed one session another's reference. The
    environment the command runs in does carry the id; where it does not, the
    session appending to its transcript at this very moment is the one that
    typed the command.
    """
    sessions = state.get("sessions") or {}
    if not sessions:
        return ""
    known = slug_for(sessions, os.environ.get("CLAUDE_CODE_SESSION_ID", ""))
    return known or max(sessions, key=lambda slug: written_at(sessions[slug]))


def written_at(record: dict) -> float:
    """When this session last wrote. No transcript is not the current folder."""
    if not record.get("transcript"):
        return 0.0
    try:
        return Path(record["transcript"]).expanduser().stat().st_mtime
    except OSError:
        return 0.0


def handoff() -> str:
    """Copies the transcript and returns a reference to the latest stretch.

    The copy ends exactly where the piece of work ended, so the number of the
    last line is the mark: the range between two calls defines the stretch
    without a single guess.
    """
    state = load("")
    slug = caller(state)
    if not slug:
        return "this folder has no registered session: SessionStart did not run here"

    record = state["sessions"][slug]
    origin = Path(record.get("transcript") or "").expanduser()
    if not origin.is_file():
        return f"transcript not found: {origin}"

    copy_transcripts(str(origin), slug)
    lines = sum(1 for _ in origin.open(encoding="utf-8", errors="ignore"))
    start = record.get("mark", 0) + 1
    if start > lines:
        # A reference to nothing would read as `#962-961`, and the agent writes
        # whatever it is handed into the memory as a source.
        return f"nothing has been written since the last handoff, at line {lines}"

    record["mark"] = lines
    record.pop("pending", None)
    save("", state, slug)
    return f"s:{slug}#{start}-{lines}"


def mark_ended() -> None:
    """Records that a session is over, so its tail can be swept in safely.

    Without it, the only way to tell a dead session from one waiting in
    another window is how long its transcript has been silent — a guess this
    turns into a fact for every session that closes in the ordinary way.
    """
    event = read_event()
    cwd = event.get("cwd", "")
    state = load(cwd)
    slug = slug_for(state["sessions"], event.get("session_id", ""))
    if not slug:
        return
    state["sessions"][slug]["ended"] = True
    save(cwd, state)


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

def mark_foreign_drift(slug: str, cwd: str) -> None:
    """Draws the line the rule guard fires on: what already drifted at start.

    Guarded by the slug the way `unfinished()` is, because this file runs its
    whole `main()` on `resume` and `compact` as well — an unguarded call would
    record the middle of a session as its beginning, and the agent's own edit
    would come back to it as someone else's. A broken sibling import must not
    take the session start down with it.
    """
    try:
        import rules
        rules.at_start(cwd, slug)
    except Exception:                      # noqa: BLE001
        pass


def main() -> None:
    if "--project" in sys.argv:
        # Memory is single-project now — the repo names itself, so there is no
        # judgement to record. Accepted as a no-op so the handoff command, which
        # still calls it, does not fall through to a spurious SessionStart.
        return
    if "--handoff" in sys.argv:
        print(handoff())
        return
    if "--ended" in sys.argv:
        mark_ended()
        return

    event = read_event()
    today = date.today()
    cwd = event.get("cwd", "")
    session_id = event.get("session_id", "")
    slug = slug_for(load(cwd)["sessions"], session_id) or session_slug(session_id, today)

    message = unfinished(slug, cwd)
    mark_foreign_drift(slug, cwd)          # before remember(): it overwrites the slug
    append_row(slug, today, morf.project())
    prepare()
    remember(slug, event.get("transcript_path", ""), cwd)
    sweep()

    for text in (message, crowding(), *due.owed(cwd)):
        if text:
            print(text)


if __name__ == "__main__":
    main()
