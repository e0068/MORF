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

    python3 due.py            what the current folder's project owes
    python3 due.py --all      every project
    python3 due.py --prompt   the same, addressed to the agent, on every turn

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

SOURCE_RE = re.compile(r"s:(\d{6}-\w+)")
ROW_RE = re.compile(r"^\|\s*s:(?P<id>[\w-]+)\s*\|[^|]*\|\s*(?P<project>[^|]*?)\s*\|")
LAST_RE = re.compile(r"^last:\s*(\S+)", re.MULTILINE)


def config(key: str, fallback):
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))[key]
    except (OSError, ValueError, KeyError):
        return fallback


# ===== Reading what is on disk =====

def order(project: str) -> list[str]:
    """This project's session ids, oldest first, as the index recorded them."""
    try:
        rows = SESSIONS.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    found = []
    for row in rows:
        match = ROW_RE.match(row)
        if match and match.group("project") == project:
            found.append(match.group("id"))
    return found


def sources(path: Path) -> set[str]:
    try:
        return set(SOURCE_RE.findall(path.read_text(encoding="utf-8")))
    except OSError:
        return set()


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
        unseen = sources(lower) - sources(upper)
        if not unseen:
            continue
        after = horizons * step ** (i - 1) if i else 0
        waited = elapsed(project, sources(upper))
        if waited >= after:
            owed.append(f"{levels[i]} → {levels[i + 1]}: {len(unseen)} session(s) never lifted, "
                        f"{waited} session(s) waited against {after}")
    return owed


def audit(project: str) -> str:
    """The skill sets the timer at ten sessions and says not to ask about it."""
    text = AUDIT.read_text(encoding="utf-8") if AUDIT.is_file() else ""
    match = LAST_RE.search(text)
    last = match.group(1) if match else "none"
    waited = elapsed(project, set() if last in ("", "none") else {last})
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


def stretch(cwd: str) -> str:
    """A piece of conversation archived and never turned into observations."""
    try:
        ref = (morf.state() / f"{morf.slot(cwd)}.pending").read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    return f"handoff: the stretch {ref} is archived and unread" if ref else ""


def owed(project: str, cwd: str = "") -> list[str]:
    """Everything this project owes. Nothing here waits on the owner."""
    if not is_project(project):
        return []
    return [line for line in (stretch(cwd), audit(project), stale_map(),
                              *consolidation(project)) if line]


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


def main() -> None:
    if "--prompt" in sys.argv:
        return as_instruction()
    projects = ([p.name for p in sorted(MEMORY.iterdir())
                 if p.is_dir() and p.name not in ("Transcripts", "Scripts", ".state")]
                if "--all" in sys.argv else [Path.cwd().name])
    for project in projects:
        for line in owed(project):
            print(f"{project}: {line}")


if __name__ == "__main__":
    main()
