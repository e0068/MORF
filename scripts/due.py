#!/usr/bin/env python3
"""What the memory owes before work starts.

Collecting was the only automatic stage. Consolidation, the fact articles
and the audit each waited for someone to read the skill and remember, and
none of them ever ran: an empty upper level looks like a correct state, so
nothing about the silence was alarming.

The owner does nothing about any of it. A debt is the agent's to discharge,
so it is put in front of the agent on every turn — not raised as a refusal
of the owner's prompt, which only made a person retype what they had just
written to pay for what an agent had forgotten.

Every condition here is already in the data, so nothing new is bookkept.
A level is owed material when the level below it carries a session the
level above has never seen, and enough of this project's sessions have
passed since. The audit counts sessions since the id in `audit.md`.

Considered and declined is a legitimate outcome — weight is often too low to
promote anything — and it discharges the debt the way every debt here does:
by being written down. The level names what it weighed on a `<!-- considered:
s:… -->` line, and a session named there is one it has seen. Inferring the
decision from the file's timestamp instead was worse than nothing; the
reasoning is in `Docs/foundation.md`.

    python3 due.py            what the current folder's project owes
    python3 due.py --all      every project
    python3 due.py --prompt   the same, addressed to the agent, on every turn
    python3 due.py --stop     refuses to let a turn end while a debt stands

No dependencies beyond the standard library.
"""

import json
import re
import sys
from pathlib import Path

import morf

# ===== Settings =====

MEMORY = morf.memory()
SESSIONS = MEMORY / "sessions.md"
AUDIT = MEMORY / "audit.md"
FACTS = morf.facts()
INDEX = MEMORY / "INDEX.md"
CONFIG_FILE = Path(__file__).with_name("config.json")
AUDIT_AFTER = 10                      # sessions, per the skill
NOT_PROJECTS = ("Transcripts", "Scripts", ".state")

SOURCE_RE = re.compile(r"s:(\d{6}-\w+)")
STRETCH_RE = re.compile(r"s:(\d{6}-\w+)#(\d+)-(\d+)")
# The verdict line, on its own line and nowhere else. It records what a level
# weighed, which is not the same as what the memory has read: left in place it
# would let a session named there pass for a stretch written up, and discharge
# a handoff debt nobody paid.
CONSIDERED_RE = re.compile(r"^[ \t]*<!--\s*considered:.*?-->[ \t]*$", re.M)
ROW_RE = re.compile(r"^\|\s*s:(?P<id>[\w-]+)\s*\|[^|]*\|\s*(?P<project>[^|]*?)\s*\|")
LAST_RE = re.compile(r"^last:\s*(\S+)", re.MULTILINE)


def config(key: str, fallback):
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))[key]
    except (OSError, ValueError, KeyError):
        return fallback


# ===== Reading what is on disk =====

def rows() -> list[tuple[str, str]]:
    """(id, project) in the order the index recorded them."""
    try:
        lines = SESSIONS.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    found = []
    for line in lines:
        match = ROW_RE.match(line)
        if match:
            found.append((match.group("id"), match.group("project")))
    return found


def order(project: str) -> list[str]:
    """This project's session ids, oldest first."""
    return [name for name, owner in rows() if owner == project]


def after(project: str, marker: str) -> int:
    """This project's sessions recorded after the marker, wherever it stood.

    The audit keeps one marker for the whole vault, so it names a session of
    whichever project was audited. Looking for it inside one project's list
    finds nothing and reports every session as unaudited.
    """
    seen = rows()
    at = next((n for n, (name, _) in enumerate(seen) if name == marker), None)
    if at is None:
        return sum(1 for _, owner in seen if owner == project)
    return sum(1 for _, owner in seen[at + 1:] if owner == project)


def sources(path: Path, weighed: bool = True) -> set[str]:
    """The sessions a level file names, verdict line included or not.

    A level *holds* what its lines cite; it has *seen* that plus what it
    weighed and declined. The two are not interchangeable. The level above
    must count a decline as seen, or the verdict closes nothing. The level
    below must not offer it as material, or a decline travels upward as
    something the next level has never received — and no line up there
    carries it, so there would be nothing to weigh.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set()
    return set(SOURCE_RE.findall(text if weighed else CONSIDERED_RE.sub("", text)))


def elapsed(project: str, since: set[str]) -> int:
    """Sessions of this project after the newest of `since`; all of them if none."""
    ids = order(project)
    positions = [i for i, name in enumerate(ids) if name in since]
    return len(ids) - (max(positions) + 1) if positions else len(ids)


# ===== The obligations =====

def consolidation(project: str) -> list[str]:
    """Levels holding material the level above has never seen, and long enough."""
    levels = config("levels", ["L0", "L1", "L2", "L3"])
    horizons, owed = config("horizon_base", 1), []
    step = config("horizon_step", 5)
    for i in range(len(levels) - 1):
        lower, upper = MEMORY / project / f"{levels[i]}.md", MEMORY / project / f"{levels[i + 1]}.md"
        unseen = sources(lower, weighed=False) - sources(upper)
        if not unseen:
            continue
        # The cadence of the level being filled: levels.md gives L1 after 1
        # session, L2 after 5, L3 after 25 — that is base * step ** i.
        after = horizons * step ** i
        waited = elapsed(project, sources(upper))
        if waited >= after:
            owed.append(f"{levels[i]} → {levels[i + 1]}: {len(unseen)} session(s) never lifted, "
                        f"{waited} session(s) waited against {after}")
    return owed


def audit(project: str) -> str:
    """The skill sets the timer at ten sessions and says not to ask about it."""
    text = AUDIT.read_text(encoding="utf-8") if AUDIT.is_file() else ""
    match = LAST_RE.search(text)
    last = match.group(1).removeprefix("s:") if match else "none"
    waited = len(order(project)) if last in ("", "none") else after(project, last)
    return f"audit: {waited} session(s) since {last}, due at {AUDIT_AFTER}" if waited >= AUDIT_AFTER else ""


def stale_map() -> str:
    """The map is built from `Facts` alone, so an article added after it is invisible."""
    articles = [p for p in FACTS.rglob("*.md")] if FACTS.is_dir() else []
    if not articles:
        return ""
    newest = max(p.stat().st_mtime for p in articles)
    if INDEX.is_file() and INDEX.stat().st_mtime >= newest:
        return ""
    return f"facts: {len(articles)} article(s) newer than the map — run build-index.py"


def is_project(project: str) -> bool:
    """A folder with shelves. The session index also names throwaway cwds."""
    levels = config("levels", ["L0", "L1", "L2", "L3"])
    return bool(project) and project != "—" and (MEMORY / project / f"{levels[0]}.md").is_file()


def pending(cwd: str) -> list[str]:
    """Stretches this folder has archived and not yet turned into observations.

    One per session, from the folder's index. A `.pending` file is what an
    earlier version wrote — one per folder, so a second dead session's stretch
    overwrote the first's. Those are still read, and clear the way any stretch
    now clears: by being handed off, which puts them in the memory as sources.
    """
    refs = []
    try:
        state = json.loads((morf.state() / f"{morf.slot(cwd)}.json").read_text(encoding="utf-8"))
        refs += [record.get("pending") for record in (state.get("sessions") or {}).values()
                 if record.get("pending")]
    except (OSError, ValueError, AttributeError):
        pass
    try:
        legacy = (morf.state() / f"{morf.slot(cwd)}.pending").read_text(encoding="utf-8").strip()
    except OSError:
        legacy = ""
    if legacy and legacy not in refs:
        refs.append(legacy)
    return refs


def read_up_to() -> dict[str, int]:
    """The last line of each session the memory already cites as a source.

    A stretch written up as an observation names itself as the source, so the
    memory is the record of what was read — evidence, where a marker is only
    bookkeeping, and bookkeeping is what went wrong. Whatever the marker says,
    lines already accounted for are not owed again.

    Every project is read, not the one being asked about: a session run in a
    worktree is a project of its own by folder name, while the observations it
    produced are written onto the shelves of the project it was work on.
    """
    highest: dict[str, int] = {}
    stems = config("levels", ["L0", "L1", "L2", "L3"]) + ["dropped"]
    for folder in sorted(MEMORY.iterdir()) if MEMORY.is_dir() else []:
        if not folder.is_dir() or folder.name in NOT_PROJECTS:
            continue
        for stem in stems:
            try:
                text = (folder / f"{stem}.md").read_text(encoding="utf-8")
            except OSError:
                continue
            for slug, _, end in STRETCH_RE.findall(CONSIDERED_RE.sub("", text)):
                highest[slug] = max(highest.get(slug, 0), int(end))
    return highest


def unread(ref: str, covered: dict[str, int]) -> str:
    """What is left of a stretch once the memory's own sources are subtracted."""
    match = STRETCH_RE.fullmatch(ref)
    if not match:
        return ref              # not a range: nothing to subtract, report it whole
    slug, start, end = match.group(1), int(match.group(2)), int(match.group(3))
    done = covered.get(slug, 0)
    if done >= end:
        return ""
    return f"s:{slug}#{max(start, done + 1)}-{end}"


def stretch(cwd: str) -> list[str]:
    """Pieces of conversation archived and never turned into observations."""
    refs = pending(cwd)
    covered = read_up_to() if refs else {}   # read only when something is claimed
    return [f"handoff: the stretch {left} is archived and unread"
            for left in (unread(ref, covered) for ref in refs) if left]


def rules_owed(project: str, cwd: str) -> list[str]:
    """What the rule layer owes, imported here rather than at module level.

    This module hangs on `UserPromptSubmit` and on `Stop`; an unhandled
    exception in a sibling would be a hook error shown to the owner on every
    turn, which is the very thing this file was written to stop doing. So a
    broken `rules.py` degrades to one line, never to the debt system going out.
    """
    try:
        import rules
        return rules.owed(project, cwd)
    except Exception:                      # noqa: BLE001 — see above
        return ["rules: bookkeeping unreadable"]


def owed(project: str, cwd: str = "") -> list[str]:
    """Everything this project owes. Nothing here waits on the owner."""
    if not is_project(project):
        return []
    return [line for line in (*stretch(cwd), audit(project), stale_map(),
                              *consolidation(project),
                              *rules_owed(project, cwd)) if line]


# ===== Entry =====

def as_instruction() -> None:
    """Puts the debt in front of the agent, on stdout, and lets the turn run.

    `UserPromptSubmit` stdout reaches the context; exit 2 would discard what
    the owner typed. The pressure is not in blocking once but in arriving
    every turn until the debt is gone — a notice said once at session start
    is what everything here was built to replace.
    """
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    cwd = event.get("cwd") or str(Path.cwd())
    debts = owed(Path(cwd).name, cwd)
    if not debts:
        return
    print("MORF: this project owes work on its memory, and it is yours to do, "
          "not the owner's to ask for. Discharge it before answering:")
    for text in debts:
        print(f"  - {text}")


def as_refusal() -> None:
    """Will not let the turn end while something is owed.

    Saying it at the start of a turn is easy to read past, because the turn
    still ends however it likes. `Stop` is the one point where the answer is
    already written and the debt is still there, so exit 2 sends it back —
    the agent finishes the work or says in the answer that it did not.

    `stop_hook_active` marks a turn already sent back once. Blocking again
    would loop, and a loop is not pressure, it is a hang.
    """
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    if event.get("stop_hook_active"):
        return
    cwd = event.get("cwd") or str(Path.cwd())
    debts = owed(Path(cwd).name, cwd)
    if not debts:
        return
    print("MORF: this turn cannot end while the memory is owed work. Discharge it, "
          "or say plainly in the answer that you are leaving it:\n  - "
          + "\n  - ".join(debts), file=sys.stderr)
    sys.exit(2)


def main() -> None:
    if "--stop" in sys.argv:
        return as_refusal()
    if "--prompt" in sys.argv:
        return as_instruction()
    projects = ([p.name for p in sorted(MEMORY.iterdir())
                 if p.is_dir() and p.name not in NOT_PROJECTS]
                if "--all" in sys.argv else [Path.cwd().name])
    for project in projects:
        for line in owed(project):
            print(f"{project}: {line}")


if __name__ == "__main__":
    main()
