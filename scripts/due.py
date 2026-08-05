#!/usr/bin/env python3
"""What the memory owes before work starts.

Collecting was the only automatic stage. Consolidation, the fact articles
and the audit each waited for someone to read the skill and remember, and
none of them ever ran: an empty upper level looks like a correct state, so
nothing about the silence was alarming.

Every condition here is already in the data, so nothing new is bookkept.
A level is owed material when the level below it carries a session the
level above has never seen, and enough of this project's sessions have
passed since. The audit counts sessions since the id in `audit.md`.

    python3 due.py            what the current folder's project owes
    python3 due.py --all      every project

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
NEGLECT = 2                           # ignored this many times over, it stops being a notice

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


def owed(project: str) -> list[tuple[str, bool]]:
    """What this project owes, each with whether it still tolerates waiting.

    An obligation is said out loud every session. It stops being a notice
    once it has been passed over `NEGLECT` times its own period: at that
    point the advisory has demonstrably lost, which this memory has already
    written down about itself once.
    """
    if not is_project(project):
        return []
    out = []
    line = stale_map()
    if line:
        out.append((line, False))
    line = audit(project)
    if line:
        waited = elapsed(project, set())
        match = LAST_RE.search(AUDIT.read_text(encoding="utf-8") if AUDIT.is_file() else "")
        last = match.group(1) if match else "none"
        if last not in ("", "none"):
            waited = elapsed(project, {last})
        out.append((line, waited >= AUDIT_AFTER * NEGLECT))
    for line in consolidation(project):
        out.append((line, False))     # crowding blocks this one, where loss is real
    return out


# ===== Entry =====

def main() -> None:
    projects = ([p.name for p in sorted(MEMORY.iterdir())
                 if p.is_dir() and p.name not in ("Transcripts", "Scripts", ".state")]
                if "--all" in sys.argv else [Path.cwd().name])
    for project in projects:
        for line, hard in owed(project):
            print(f"{project}: {line}" + ("  [blocking]" if hard else ""))


if __name__ == "__main__":
    main()
