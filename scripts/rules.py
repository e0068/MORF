#!/usr/bin/env python3
"""The rule layer's bookkeeping: what MORF put into files it does not own.

Rules are the only layer living outside MORF, and that costs three things:
    their text must sit where it loads from, in a file anyone may rewrite;
    without a record MORF cannot say which rules exist or where;
    a rule edited by a foreign hand disappears unnoticed.

So each watched file gets a pair inside the contour:
    `*.snap.md` — the file as it stood when its rules were last accounted for;
    `*.log.md`  — written by hand, saying what became of them.

Counters live in `map.md` and never outside, because writing our numbers into
someone's `CLAUDE.md` on every handoff would mean a machine rewriting a file
that is not ours.

    python3 rules.py                    what this project's watched files owe
    python3 rules.py --track PATH       take a file under watch
    python3 rules.py --adopt PATH TEXT  take an item already in the file
    python3 rules.py --diff [PATH]      which rules moved
    python3 rules.py --seal PATH        seal after the log is written
    python3 rules.py --forget PATH      stop watching; the log stays

No dependencies beyond the standard library.
"""

import difflib
import json
import re
import sys
from pathlib import Path

import morf

# ===== Where things are =====

RULES = morf.home() / "Rules"
MAP = RULES / "map.md"

# The five addresses, as a fixed table.
#
# The root is cwd for a project and `~/.claude` for `home`, because:
#   `due.py` already takes the project from the folder name, and
#   a second source of truth about where a project lies goes stale on the
#   first move.
#
# The folder prefix differs by scope:
#   under `home` these sit directly in `~/.claude`;
#   inside a project they all sit under `<root>/.claude`.
# Getting that wrong makes three of the eight combinations untrackable while
# looking like it works for the other five.
SHAPES = (
    ("Paths",  "rules",  "md"),
    ("Agents", "agents", "md"),
    ("Skills", "skills", "SKILL"),
)


def under(scope: str, folder: str) -> Path:
    return Path(folder) if scope == "home" else Path(".claude") / folder


BULLET_RE = re.compile(r"^\s*[-*+]\s+(?P<text>\S.*?)\s*$")
ENTRY_RE = re.compile(
    r"^\s*[-*+]\s+(?P<verb>added|widened|narrowed|returned|outside):\s+(?P<body>.+?)\s*$"
)
# The source closes the entry: `body (s:…) — reason`.
# Everything after it is prose for a human, everything before it is the body.
#
# Three anchors were tried inside the body and each truncated real rules:
#   an em dash — rule texts in these notes are full of them;
#   square brackets — `do not touch [S= R= t=]` is MORF's own vocabulary;
#   the source as a landmark — `(by hand)` is ordinary English and `(s:ref)`
#     is what this project writes about itself, so a rule can hold either.
#
# A delimiter picked from characters that occur in rule text keeps failing
# whichever one is picked. So the source is validated, not searched for:
#   it must end the entry, or be followed by the reason;
#   exactly one candidate must qualify;
#   none or several, and the entry is broken rather than guessed.
SOURCE_RE = re.compile(r"\((?:s:[^)]*|by hand)\)")


def home_root() -> Path:
    return Path.home() / ".claude"


def scope_root(scope: str, cwd: Path) -> Path:
    """`home` hangs off `~/.claude`, anything else off the working folder."""
    return home_root() if scope == "home" else cwd


def address(scope: str, relative: Path, cwd: Path) -> Path:
    """Snapshot path inside a scope -> the real file, with `.snap` dropped."""
    root = scope_root(scope, cwd)
    parts = relative.parts
    name = relative.name.replace(".snap.md", ".md")
    if len(parts) == 1:                                   # CLAUDE.snap.md
        return root / name
    folder, rest = parts[0], parts[1:]
    for label, place, _ in SHAPES:
        if folder != label:
            continue
        return root.joinpath(under(scope, place), *rest[:-1], name)
    return root.joinpath(*parts[:-1], name)


def snapshot_of(path: Path, cwd: Path) -> tuple[str, Path] | None:
    """The real file -> (scope, snapshot path relative to the scope folder).

    Returns None for a file at none of the five addresses:
        `--track` refuses it rather than inventing a place,
        because the reverse mapping has to stay total in both directions.
    """
    path = path.expanduser().resolve()
    for scope, root in (("home", home_root()), (cwd.name, cwd)):
        root = root.expanduser().resolve()
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        parts = rel.parts
        if len(parts) == 1 and parts[0] == "CLAUDE.md":
            return scope, Path("CLAUDE.snap.md")
        for label, place, kind in SHAPES:
            under_parts = under(scope, place).parts
            if parts[:len(under_parts)] != under_parts:
                continue
            tail = Path(*parts[len(under_parts):])
            if kind == "SKILL" and tail.name != "SKILL.md":
                continue
            return scope, Path(label) / tail.with_name(tail.name.replace(".md", ".snap.md"))
    return None


def pair(scope: str, relative: Path) -> tuple[Path, Path]:
    """Snapshot and log for one watched file."""
    snap = RULES / scope / relative
    log = snap.with_name(snap.name.replace(".snap.md", ".log.md"))
    return snap, log


# ===== What the log claims =====

def split_source(text: str) -> tuple[str, bool]:
    """(body, whether the entry is properly closed by exactly one source)."""
    fit = [found for found in SOURCE_RE.finditer(text)
           if not text[found.end():].strip()
           or text[found.end():].lstrip().startswith("—")]
    if len(fit) != 1:
        return text.strip(), False
    body = text[:fit[0].start()].strip()
    # A source-shaped token surviving in the body is not an error: a rule in
    # these notes may legitimately quote one, and `write (s:ref) on every line`
    # is exactly such a rule. A pasted-twice source looks identical, and it is
    # the cheaper failure — the claim then matches nothing in the file and is
    # reported as drift, whereas rejecting the body would make a legitimate
    # rule untrackable for good.
    return body, True


def closed(text: str) -> bool:
    return split_source(text)[1]


def entries(log: Path) -> list[tuple[str, str]]:
    """(verb, body) per entry, joining wrapped lines.

    The logs are written by hand and wrap like the rest of these notes, so an
    indented line continues the one above it. The run ends at:
        a closed entry — the source is its terminator;
        a blank line;
        any unindented line.
    Without those three a nested bullet, or an indented note under a later
    heading, would be swallowed into a rule that closed sessions ago.
    """
    try:
        lines = log.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    found: list[tuple[str, str]] = []
    open_entry = False
    for line in lines:
        entry = ENTRY_RE.match(line)
        if entry:
            found.append((entry.group("verb"), entry.group("body")))
            open_entry = not closed(entry.group("body"))
            continue
        if not line.strip() or not line.startswith((" ", "\t")):
            open_entry = False                            # blank line or a heading closes it
            continue
        if not open_entry:
            continue                                      # a nested bullet is not a wrap
        verb, body = found[-1]
        found[-1] = (verb, f"{body} {line.strip()}")
        open_entry = not closed(found[-1][1])
    return found


def split_move(body: str, live: list[str]) -> tuple[str, str] | None:
    """Splits `old → new` where the rule's own text may contain an arrow.

    The split is checked, not guessed: the real separator is the cut whose
    left side is a rule the file actually holds. When none is:
        `None` says the entry is not resolvable;
        a guess would append a rule text that exists nowhere;
        and every later entry consulting `live` would inherit the phantom.
    """
    parts = body.split("→")
    if len(parts) < 2:
        return (body.strip(), "") if body.strip() in live else None
    for cut in range(1, len(parts)):
        left = "→".join(parts[:cut]).strip()
        if left in live:
            return left, "→".join(parts[cut:]).strip()
    return None


def replay(log: Path) -> tuple[list[str], list[str]]:
    """(rules the file holds now, entries that could not be resolved).

    The set is not stored anywhere:
        the log already records every arrival and departure;
        a second copy would be one more thing to go stale.

    An entry the replay cannot resolve is a defect in the record, and is
    reported as one — staying silent about it is worse than a debt about it.
    """
    live: list[str] = []
    broken: list[str] = []
    for verb, raw in entries(log):
        body, whole = split_source(raw)
        if not whole:
            # No source, or several that could be one: invalid exactly as a
            # memory line without sources is. It claims nothing and is reported.
            broken.append(f"{verb}: {body}")
            continue
        if verb == "outside":
            continue
        if verb == "added":
            if body not in live:                          # adding twice is one rule
                live.append(body)
            continue
        move = split_move(body, live)
        if move is None:
            broken.append(f"{verb}: {body}")
            continue
        left, right = move
        live.remove(left)
        if verb == "narrowed" and right and not right.startswith("@"):
            live.append(right)                            # reworded, still here
    return live, broken



def items(path: Path) -> list[str]:
    """Every list item in the file. Which of them are rules, the log says."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    found = []
    for line in lines:
        bullet = BULLET_RE.match(line)
        if bullet:
            found.append(bullet.group("text"))
    return found


def unaccounted(path: Path, cwd: Path) -> tuple[list[str], list[str], list[str]]:
    """(gone or changed, added by hand, unresolvable log entries).

    gone     — the log knows these rules and the file no longer holds them;
    extra    — items the log does not know;
    broken   — a log entry that does not read back.

    Only the first is a debt, and `extra` is not reported anywhere: MORF
    accounts for what it wrote into a file and for nothing else. An item the
    owner put there is theirs, works as it always did, and is not this layer's
    to notice, propose or chase. It enters only on the owner's explicit word,
    through `--adopt`, which is why that command is never suggested.
    """
    found = snapshot_of(path, cwd)
    if not found:
        return [], [], []
    scope, relative = found
    snap, log = pair(scope, relative)
    if not snap.exists():
        return [], [], []
    present = items(path)
    known, broken = replay(log)
    gone = [rule for rule in known if rule not in present]
    extra = [item for item in present if item not in known]
    return gone, extra, broken


# ===== What is watched =====

def outside_rules(path: Path, snap: Path, log: Path) -> int:
    """Lines that changed since the seal without touching a known rule.

    This is the snapshot's one job. Drift is read from the log, which knows
    what the file should hold; what the log cannot know is how much else
    moved — and `outside:` in the log is exactly that count. Without this the
    snapshot would store a copy nobody reads and the verb would have no
    producer.

    The filter is membership, not shape, and it excludes both sides.

    Shape alone would drop a reworded prose bullet out of every report at
    once: the log never claimed it, so it is not `gone`; it was a candidate
    before and after, so `extra` does not move; and as a list item it would be
    skipped here too. So a changed line counts unless it is a bullet the file
    or the log accounts for elsewhere:

        a rule the log knows      — already reported as `gone`;
        an item the file now has  — already reported as `extra`.

    Excluding only the first would count the new half of an in-place rule
    edit, and `outside:` reads "no rule touched" — asserting that about the
    one line where a rule was touched. What remains counted is what nothing
    else names: a removed bullet nobody accounted for, and prose.
    """
    try:
        was = snap.read_text(encoding="utf-8").splitlines()
        now = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    accounted = set(replay(log)[0]) | set(items(path))
    moved = 0
    for line in difflib.unified_diff(was, now, n=0, lineterm=""):
        if line[:1] not in ("+", "-") or line[:3] in ("+++", "---"):
            continue
        bullet = BULLET_RE.match(line[1:])
        if not (bullet and bullet.group("text") in accounted):
            moved += 1
    return moved


def watched(cwd: Path) -> list[tuple[str, Path]]:
    """Every watched file of this project plus everything under `home`."""
    if not RULES.is_dir():
        return []
    out = []
    for scope in ("home", cwd.name):
        folder = RULES / scope
        if not folder.is_dir():
            continue
        for snap in sorted(folder.rglob("*.snap.md")):
            out.append((scope, snap.relative_to(folder)))
    return out


# ===== The debt =====

def owed(project: str, cwd: str = "") -> list[str]:
    """What the rule layer owes. Reads only; writes nothing.

    cwd is normalised the way `morf.slot()` does it, because:
        `due.py` calls this without cwd on both of its paths;
        `Path("").name` is empty;
        so the check would silence the useful case along with the foreign one.
    """
    here = Path(cwd).expanduser() if cwd else Path.cwd()
    if here.name != project or not RULES.is_dir():
        return []
    debts = []
    for scope, relative in watched(here):
        # One unreadable file must not silence the debts of all the others.
        try:
            target = address(scope, relative, here)
            if not target.exists():
                debts.append(f"rules: {target} is gone while MORF still watches it")
                continue
            gone, _, broken = unaccounted(target, here)
        except Exception:                      # noqa: BLE001
            debts.append(f"rules: {relative} cannot be read")
            continue
        if gone:
            debts.append(f"rules: {target.name} changed and {len(gone)} rule(s) are "
                         f"unaccounted — run rules.py --diff")
        if broken:
            debts.append(f"rules: {len(broken)} entr(ies) in {target.name}'s log cannot be "
                         f"read back — run rules.py --diff")
    # Items the log does not know are candidates, not debts: telling an added
    # rule from added prose is impossible here, and charging for prose would
    # make every freshly tracked file owe on every turn forever. They show up
    # in `--diff` and nowhere else.
    return debts


# ===== Drift as of the session start =====

def at_start(cwd: str, slug: str) -> None:
    """Records what already drifted before this session touched anything.

    The guard fires on *foreign* drift only, so it needs a line drawn at the
    start. Without it the agent blocks itself:
        it writes a rule;
        the file diverges from the snapshot;
        its next edit is refused by a diff of its own work one turn ago.

    Guarded by the slug exactly as `unfinished()` is, because `SessionStart`
    runs on `resume` and `compact` too, and rewriting the list there would
    record the middle of a session as its beginning.
    """
    here = Path(cwd).expanduser() if cwd else Path.cwd()
    current = morf.state() / f"{morf.slot(cwd)}.json"
    try:
        if json.loads(current.read_text(encoding="utf-8")).get("slug") == slug:
            return
    except (OSError, ValueError):
        pass
    drifted = []
    for scope, relative in watched(here):
        target = address(scope, relative, here)
        gone, _, _ = unaccounted(target, here)
        if gone:
            drifted.append(str(target))
    path = morf.state() / f"{morf.slot(cwd)}.rules"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(drifted), encoding="utf-8")


def foreign(cwd: str) -> set[str]:
    """Paths that were already drifted when the session began."""
    try:
        raw = (morf.state() / f"{morf.slot(cwd)}.rules").read_text(encoding="utf-8")
    except OSError:
        return set()
    return {line for line in raw.splitlines() if line}


# ===== The register =====

def section(scope: str, relative: Path, cwd: Path) -> str:
    return f"## {address(scope, relative, cwd)} — {scope}"


def map_add_section(header: str) -> None:
    """`map.md` is edited in place and never rebuilt: it is the only copy of
    the counters, and a rebuild would erase them on the first seal."""
    MAP.parent.mkdir(parents=True, exist_ok=True)
    text = MAP.read_text(encoding="utf-8") if MAP.exists() else "# Rule register\n"
    if header not in text:
        text = text.rstrip() + f"\n\n{header}\n"
    MAP.write_text(text, encoding="utf-8")


def map_add_rule(header: str, text: str, source: str) -> None:
    body = MAP.read_text(encoding="utf-8") if MAP.exists() else "# Rule register\n"
    lines = body.splitlines()
    if header not in lines:
        lines += ["", header]
    at = lines.index(header) + 1
    while at < len(lines) and not lines[at].startswith("## "):
        at += 1
    lines.insert(at, f"- hit:0 use:0 {text} (s:{source})")
    MAP.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ===== Commands =====

def session_id(cwd: str) -> str:
    try:
        state = json.loads((morf.state() / f"{morf.slot(cwd)}.json").read_text(encoding="utf-8"))
        return state.get("slug", "")
    except (OSError, ValueError):
        return ""


def track(raw: str, cwd: Path) -> int:
    found = snapshot_of(Path(raw), cwd)
    if not found:
        print(f"Not one of the five addresses: {raw}")
        return 1
    scope, relative = found
    target = address(scope, relative, cwd)
    if not target.exists():
        print(f"No such file: {target}")
        return 1
    snap, log = pair(scope, relative)
    snap.parent.mkdir(parents=True, exist_ok=True)
    fresh = not snap.exists()
    if not fresh:
        # Idempotent on purpose: the skill tells the agent to track a file if
        # it is not watched yet, and nothing answers "is it watched" — so this
        # is the check, and a check must not fail on the desired state.
        #
        # The snapshot is left alone. Rewriting it would move its mtime above
        # the log's, and `--seal` in a folder with no registered session falls
        # back to exactly that comparison: a re-track would make the next seal
        # refuse.
        print(f"Already watched: {target}. Use --diff to see what moved.")
    else:
        snap.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    if not log.exists():
        log.write_text(f"---\nname: {scope}-{relative.name.replace('.snap.md', '')}-log\n"
                       f"address: {target}\n---\n", encoding="utf-8")
    map_add_section(section(scope, relative, cwd))
    if fresh:
        print(f"Watching {target}.")
    return 0


def adopt(raw: str, text: str, cwd: Path) -> int:
    """Takes a line MORF did not write. Only ever on the owner's own word.

    The layer watches what it generated. An instruction the owner wrote is
    theirs: not a candidate, not a proposal, not something to ask about. This
    command exists so that an older rule can still be brought in when they
    decide to, and for no other reason — nothing in the system offers it.

    The source is the current session, and it marks when MORF started counting,
    not where the rule came from: `/why` on it reaches the adoption and no
    further.
    """
    found = snapshot_of(Path(raw), cwd)
    if not found:
        print(f"Not one of the five addresses: {raw}")
        return 1
    scope, relative = found
    target = address(scope, relative, cwd)
    if text not in items(target):
        print(f"No such item in {target}: {text}")
        return 1
    snap, log = pair(scope, relative)
    if not snap.exists():
        print(f"Not watched yet: {target}. Run --track first.")
        return 1
    slug = session_id(str(cwd)) or "unregistered"
    body = log.read_text(encoding="utf-8") if log.exists() else ""
    head = f"## s:{slug}"
    # The log is grouped by session; adopting three items in one session must
    # not produce three identical headings.
    opening = "" if body.rstrip().endswith(head) or f"\n{head}\n" in body else f"\n{head}\n"
    with log.open("a", encoding="utf-8") as handle:
        handle.write(f"{opening}\n- added: {text} (s:{slug})\n")
    map_add_rule(section(scope, relative, cwd), text, slug)
    print(f"Adopted into {target}: {text}")
    return 0


def diff(cwd: Path, only: str = "") -> int:
    shown = 0
    for scope, relative in watched(cwd):
        target = address(scope, relative, cwd)
        if only and Path(only).expanduser().resolve() != target:
            continue
        gone, _, broken = unaccounted(target, cwd)
        snap_here, log_here = pair(scope, relative)
        if not gone and not broken and not outside_rules(target, snap_here, log_here):
            continue
        shown += 1
        print(f"\n{target}")
        for rule in gone:
            print(f"  − {rule}")
        for entry in broken:
            print(f"  ! {entry}   (this log entry does not read back)")
        snap, log = pair(scope, relative)
        moved = outside_rules(target, snap, log)
        if moved:
            print(f"  · {moved} line(s) changed outside the rules since the last seal")
    if not shown:
        print("Nothing moved.")
    return 0


def seal(raw: str, cwd: Path) -> int:
    found = snapshot_of(Path(raw), cwd)
    if not found:
        print(f"Not one of the five addresses: {raw}")
        return 1
    scope, relative = found
    target = address(scope, relative, cwd)
    snap, log = pair(scope, relative)
    slug = session_id(str(cwd))
    if slug:
        if f"## s:{slug}" not in (log.read_text(encoding="utf-8") if log.exists() else ""):
            print(f"The log has no entry for this session. Describe the change first.")
            return 1
    else:
        # No session registered here — SessionStart never ran in this folder.
        # Refusing forever would make the guard permanent, so the promise is
        # held by a check that needs no identifier.
        if not (log.exists() and snap.exists() and log.stat().st_mtime >= snap.stat().st_mtime):
            print("This folder has no registered session, and the log is not newer "
                  "than the snapshot. Describe the change first.")
            return 1
        print("This folder has no registered session: sealing against the log's age.")
    snap.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    path = morf.state() / f"{morf.slot(str(cwd))}.rules"
    if path.exists():
        kept = [line for line in path.read_text(encoding="utf-8").splitlines()
                if line and line != str(target)]
        path.write_text("\n".join(kept), encoding="utf-8")
    print(f"Sealed {target}.")
    return 0


def forget(raw: str, cwd: Path) -> int:
    """The snapshot goes, the log and the register stay: counters are history."""
    found = snapshot_of(Path(raw), cwd)
    if not found:
        print(f"Not one of the five addresses: {raw}")
        return 1
    scope, relative = found
    snap, _ = pair(scope, relative)
    if snap.exists():
        snap.unlink()
    header = section(scope, relative, cwd)
    if MAP.exists():
        # Per section, not per file: once any section carried the mark, a
        # file-wide test would silently skip every later `--forget`.
        lines = MAP.read_text(encoding="utf-8").splitlines()
        lines = [f"{line} — no longer watched" if line == header else line
                 for line in lines]
        MAP.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"No longer watching {address(scope, relative, cwd)}. The log stays.")
    return 0


# ===== Entry =====

def main() -> int:
    argv = sys.argv[1:]
    cwd = Path.cwd()
    if "--track" in argv:
        return track(argv[argv.index("--track") + 1], cwd)
    if "--adopt" in argv:
        at = argv.index("--adopt")
        return adopt(argv[at + 1], " ".join(argv[at + 2:]), cwd)
    if "--diff" in argv:
        at = argv.index("--diff")
        return diff(cwd, argv[at + 1] if len(argv) > at + 1 else "")
    if "--seal" in argv:
        return seal(argv[argv.index("--seal") + 1], cwd)
    if "--forget" in argv:
        return forget(argv[argv.index("--forget") + 1], cwd)
    for line in owed(cwd.name, str(cwd)):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
