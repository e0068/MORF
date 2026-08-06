#!/usr/bin/env python3
"""What moved in memory, as a matrix read from disk rather than a claim.

A trace the agent writes is a self-report — the one thing this system refuses
to trust, for the same reason `use` is the number it cannot verify. So the
trace is not written, it is derived: memory is a set of files, every stage is
a mutation of them, and movement is the difference between two readings of the
disk. Nothing here is taken on the word that a step happened; a line counts as
moved only because it now sits in a different file than it did.

Identity survives a move. Consolidation strips and rewrites `[S= R= t=]`, but a
line keeps its text and its sources across every promotion, return and drop. So
two readings keyed on (text, sources) tell, per shelf and per level, what
arrived and what left — `count (+in −out)` in a cell, state and movement at once.
Facts and Rules diff the same way and ride the same table as their own rows.

    trace.py --mark      snapshot the baseline (SessionStart)
    trace.py --report    against the baseline, if it moved (Stop)
    trace.py --show       always, moved or not (the command)

Each render goes two ways: printed plain for the chat, and written to
`Memory/TRACE.md` with each stirred cell a markdown link to its own heading, so
the matrix is clickable inside Obsidian — a cell lands on the lines behind it.

No dependencies beyond the standard library.
"""

import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import morf

MEMORY = morf.memory()
FACTS = morf.facts()
STATE = morf.state()
RULES_MAP = morf.home() / "Rules" / "map.md"
NOTE = MEMORY / "TRACE.md"               # generated view, clickable inside Obsidian
CONFIG_FILE = Path(__file__).with_name("config.json")

# The counters and the score block are rewritten in place, so neither may enter
# the identity; the text and the sources are what a line carries across a move.
# Anchored on `S=`, like score-memory.py, so a `[[link]]` at the start of the
# text is not mistaken for the block. The counter set must stay in step with
# score-memory.py's LINE_RE: a name it strips and this does not would fall into
# the text and shift every already-scored line's hash for one turn.
LINE_RE = re.compile(
    r"^- (?:↑ )?"
    r"(?:hit:\d+)? ?(?:use:\d+)? ?(?:miss:\d+)? ?(?:inverse:\d+)? ?"
    r"(?:\[S=[^\]]*\])?"
    r"(?P<text>.+?)"
    r"\((?P<sources>s:[^)]*)\)\s*$"
)


def config(key, fallback):
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))[key]
    except (OSError, ValueError, KeyError):
        return fallback


def columns() -> list[str]:
    """The levels, then the one shelf that has no limit and no return."""
    return config("levels", ["L0", "L1", "L2", "L3"]) + ["dropped"]


def shelves() -> list[str]:
    """Folders under Memory that carry the first level file. The session index
    also names throwaway cwds; a shelf is the folder with the files."""
    first = columns()[0]
    skip = {"Transcripts", "Scripts", ".state"}
    try:
        return sorted(p.name for p in MEMORY.iterdir()
                      if p.is_dir() and p.name not in skip
                      and (p / f"{first}.md").is_file())
    except OSError:
        return []


def identity(line: str) -> str | None:
    """A fingerprint that outlives a move: the text and the sources, hashed.

    The `↑` mark — a rule proposed for the line — is metadata, not content, and
    it sits after `- ` in a level but mid-line in some dropped entries. It is
    stripped either way, so the same line hashes alike wherever it stands."""
    match = LINE_RE.match(line)
    if not match:
        return None
    text = match.group("text").strip().lstrip("↑").strip()
    key = f"{text}␟{match.group('sources').strip()}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def cell(shelf: str, column: str) -> Counter:
    """The line identities in one shelf-level file, as a multiset."""
    try:
        lines = (MEMORY / shelf / f"{column}.md").read_text(encoding="utf-8").splitlines()
    except OSError:
        return Counter()
    return Counter(h for h in (identity(line) for line in lines) if h)


def fact_ids() -> list[str]:
    """Each article as a path under Facts — the identity a new article changes
    and a move never touches, so an addition shows as an addition."""
    if not FACTS.is_dir():
        return []
    return sorted(str(p.relative_to(FACTS)) for p in FACTS.rglob("*.md"))


def rule_ids() -> list[str]:
    """Each register line by the identity a memory line carries, so a rule
    adopted or returned reads off the same diff the levels do."""
    try:
        lines = RULES_MAP.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    return sorted(h for h in (identity(line) for line in lines) if h)


def rule_texts() -> dict[str, str]:
    """hash → readable text of a register line, for naming what was adopted."""
    texts = {}
    try:
        for line in RULES_MAP.read_text(encoding="utf-8").splitlines():
            match = LINE_RE.match(line)
            if match:
                texts[identity(line)] = match.group("text").strip().lstrip("↑").strip()
    except OSError:
        pass
    return texts


def snapshot() -> dict:
    """The whole of memory as identities — the baseline, kept as hashes and
    paths so no line's text is copied out of the folder."""
    return {
        "shelves": {s: {c: dict(cell(s, c)) for c in columns()} for s in shelves()},
        "facts": fact_ids(),
        "rules": rule_ids(),
    }


# ===== Baseline on disk =====

def baseline_path(cwd: str) -> Path:
    return STATE / f"{morf.slot(cwd)}.trace.json"


def mark(cwd: str) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    baseline_path(cwd).write_text(json.dumps(snapshot()), encoding="utf-8")


def load_baseline(cwd: str) -> dict | None:
    try:
        return json.loads(baseline_path(cwd).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# ===== The matrix =====

def side(reading: dict, shelf: str, column: str) -> Counter:
    return Counter((reading.get("shelves", {}).get(shelf) or {}).get(column, {}))


def flow(before: dict, now: dict, shelf: str, column: str) -> tuple[int, int, int]:
    """(arrived, held now, left) for one cell — pure multiset difference."""
    was, has = side(before, shelf, column), side(now, shelf, column)
    return sum((has - was).values()), sum(has.values()), sum((was - has).values())


def change_str(arrived: int, left: int) -> str:
    """The round's movement: `+3`, `−2`, `+1 −2`, or empty when a cell held."""
    return " ".join(p for p in (f"+{arrived}" if arrived else "",
                                f"−{left}" if left else "") if p)


def cell_body(arrived: int, count: int, left: int) -> str:
    """The plain cell for the chat: the standing count at the round's end, then
    in brackets what it added and took away. `17`, `17 (+3)`, `3 (+1 −2)`."""
    change = change_str(arrived, left)
    return f"{count} ({change})" if change else str(count)


# ===== Which lines moved =====

def locations(reading: dict, shelf: str) -> dict[str, str]:
    """hash → the column it sits in, for one shelf in one reading."""
    return {h: col for col, counts in (reading.get("shelves", {}).get(shelf) or {}).items()
            for h in counts}


def line_texts(shelf: str) -> dict[str, str]:
    """hash → readable text, recovered from the shelf as it stands now. Nothing
    is ever deleted, so a line that left a cell still sits in the one it entered
    — its text is on disk to be read, and none of it is kept in the baseline."""
    texts = {}
    for column in columns():
        try:
            lines = (MEMORY / shelf / f"{column}.md").read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            match = LINE_RE.match(line)
            if match:
                texts[identity(line)] = match.group("text").strip().lstrip("↑").strip()
    return texts


def moves_of(before: dict, now: dict, shelf: str) -> list[tuple]:
    """(origin, dest, hash) for every line that changed column in one shelf.
    `origin` is None for a birth (a fresh observation, a returned rule); `dest`
    is None only for the impossible vanish, since nothing is ever deleted."""
    was, has = locations(before, shelf), locations(now, shelf)
    return [(was.get(h), has.get(h), h) for h in set(was) | set(has)
            if was.get(h) != has.get(h)]


def clip(text: str, width: int = 100) -> str:
    text = " ".join(text.split())
    return f"«{text[:width]}…»" if len(text) > width else f"«{text}»"


def anchor(shelf: str, column: str) -> str:
    """The heading a cell links to — one per shelf-level, so a click lands on
    exactly the lines behind that cell."""
    return f"{shelf} · {column}"


def note_link(head: str, text: str) -> str:
    """A markdown link to a heading in the same note. It carries no pipe to
    escape, so unlike a wikilink alias it stays clickable inside a table cell.
    The fragment is the heading text, percent-encoded the way Obsidian matches
    it — the plain-space form (`#a b`) does not resolve, the encoded one does."""
    return f"[{text}](#{quote(head)})"


def cell_link(shelf: str, column: str, arrived: int, count: int, left: int) -> str:
    """The cell for the note, split so state and change are separate clicks: the
    count opens the whole list (the level's own file), the `(+in −out)` jumps to
    the heading that names exactly what moved this round."""
    whole = f"[{count}]({quote(shelf)}/{column}.md)" if count else "0"
    change = change_str(arrived, left)
    return f"{whole} ({note_link(anchor(shelf, column), change)})" if change else whole


def sections(before: dict, now: dict, stirred: list[str]) -> list[str]:
    """Per shelf a `### {shelf}` heading, and under it a `#### {shelf} · {col}`
    per moved cell, listing the lines that arrived (`←`) and left (`→`). Both are
    same-note anchors, so a shelf name and a cell each land on their own lines.
    `dropped` gathers every channel into its one heading."""
    blocks = []
    for shelf in stirred:
        texts = line_texts(shelf)
        cells: dict[str, dict[str, list]] = {}
        for origin, dest, h in moves_of(before, now, shelf):
            if dest is not None:
                cells.setdefault(dest, {}).setdefault("in", []).append((origin, h))
            if origin is not None:
                cells.setdefault(origin, {}).setdefault("out", []).append((dest, h))
        part = [f"### {shelf}"]
        for column in columns():
            if column not in cells:
                continue
            part.append(f"#### {anchor(shelf, column)}")
            for origin, h in cells[column].get("in", []):
                part.append(f"- ← {origin or 'new'}: {clip(texts.get(h, '(text gone)'))}")
            for dest, h in cells[column].get("out", []):
                part.append(f"- → {dest or 'gone'}: {clip(texts.get(h, '(text gone)'))}")
        blocks.append("\n".join(part))
    return blocks


def deltas(before_ids, now_ids: list[str]) -> tuple[list[str], list[str]]:
    """(added, removed) between two id lists. A side that is absent or from an
    older baseline format counts as no change, never as a wholesale add."""
    was = set(before_ids) if isinstance(before_ids, list) else set(now_ids)
    return sorted(set(now_ids) - was), sorted(was - set(now_ids))


def row_label(name: str, note_target: str, chat_target: Path, link: bool) -> str:
    """A row's name links to where its lines live — the folder inside the note
    (Obsidian opens the path), the absolute path in the chat (the app does). One
    click to arrive at the shelf, kept apart from the count and the change."""
    return f"[{name}]({note_target if link else chat_target})"


def tally_row(name: str, note_target: str, chat_target: Path, count: int,
              added: list, removed: list, link: bool) -> str | None:
    """Facts and Rules are outcomes without levels: one tally in the first
    column, the rest blank. The count opens their file, the `(+in −out)` jumps
    to the heading naming what changed. Shown only if it stands or it moved."""
    if not count and not added and not removed:
        return None
    change = change_str(len(added), len(removed))
    if link:
        whole = f"[{count}]({note_target})" if count else "0"
        body = f"{whole} ({note_link(name, change)})" if change else whole
    else:
        body = cell_body(len(added), count, len(removed))
    cells = [body] + [""] * (len(columns()) - 1)
    return f"| {row_label(name, note_target, chat_target, link)} | {' | '.join(cells)} |"


def tally_section(name: str, added: list[str], removed: int, gone: str) -> str | None:
    if not added and not removed:
        return None
    part = [f"### {name}", *[f"- + {line}" for line in added]]
    if removed:
        part.append(f"- − {removed} {gone}")
    return "\n".join(part)


def build(before: dict, now: dict, always: bool, link: bool) -> str:
    """The matrix as a markdown table — a shelf per row, a level per column, the
    cell `count (+in −out)` — with Facts and Rules appended as their own rows.
    `link` turns every moved cell and name into a same-note markdown link, and
    under the table a heading per one lists exactly the lines behind it."""
    cols = columns()
    names = sorted(set(now["shelves"]) | set(before.get("shelves", {})))

    moved, rows, stirred = False, [], []
    for shelf in names:
        cells, alive, stir = [], False, False
        for column in cols:
            arrived, count, left = flow(before, now, shelf, column)
            alive = alive or count
            stir = stir or arrived or left
            cells.append(cell_link(shelf, column, arrived, count, left) if link
                         else cell_body(arrived, count, left))
        moved = moved or stir
        if stir:
            stirred.append(shelf)
        # A shelf empty and unmoved is a throwaway cwd, not a memory — skip it.
        if alive or stir:
            # Obsidian will not open a bare folder link, so the name opens the
            # shelf's inbox file, which reveals the folder and all its levels.
            first = f"{quote(shelf)}/{columns()[0]}.md"
            rows.append(f"| {row_label(shelf, first, MEMORY / shelf / f'{columns()[0]}.md', link)} | {' | '.join(cells)} |")

    facts_added, facts_removed = deltas(before.get("facts"), now["facts"])
    rules_added, rules_removed = deltas(before.get("rules"), now["rules"])
    rows += [r for r in (
        tally_row("Facts", "INDEX.md", MEMORY / "INDEX.md", len(now["facts"]), facts_added, facts_removed, link),
        tally_row("Rules", "../Rules/map.md", RULES_MAP, len(now["rules"]), rules_added, rules_removed, link),
    ) if r]
    moved = moved or facts_added or facts_removed or rules_added or rules_removed
    if not moved and not always:
        return ""

    header = f"| Shelf | {' | '.join(cols)} |"
    ruler = "|" + "---|" * (len(cols) + 1)
    title = "MORF — what moved this session" if moved else "MORF memory"
    # The one line not derived from disk: the moment this view was drawn —
    # metadata about the rendering, not a claim about what moved.
    out = [title, f"_{datetime.now().strftime('%Y-%m-%d %H:%M')}_", "", header, ruler, *rows]

    rtx = rule_texts() if rules_added else {}
    blocks = sections(before, now, stirred) + [b for b in (
        tally_section("Facts", [f"`{p}`" for p in facts_added], len(facts_removed), "removed"),
        tally_section("Rules", [clip(rtx.get(h, "(text gone)")) for h in rules_added],
                      len(rules_removed), "returned to memory"),
    ) if b]
    if blocks:
        out += ["", "**Moved** — a heading per row and cell; click one to land on its lines:",
                "", "\n\n".join(blocks)]
    return "\n".join(out)


def write_note(text: str) -> None:
    """The clickable copy, regenerated whenever a turn moved memory."""
    try:
        NOTE.write_text("> Generated by `trace.py` on every turn that moves "
                        "memory. Do not edit.\n\n" + text + "\n", encoding="utf-8")
    except OSError:
        pass


def emit(cwd: str, always: bool) -> None:
    """Write the markdown-linked note for Obsidian, print the plain one for chat."""
    now = snapshot()
    before = load_baseline(cwd) or now       # no baseline yet is no movement
    note = build(before, now, always, link=True)
    if note:
        write_note(note)
    chat = build(before, now, always, link=False)
    if chat:
        print(chat)


# ===== Entry =====

def hook_cwd() -> str:
    """A hook is handed its event on stdin; the command is not, so this is only
    read in the hook modes and never in --show, where stdin would block."""
    try:
        return json.load(sys.stdin).get("cwd") or str(Path.cwd())
    except (json.JSONDecodeError, ValueError, OSError):
        return str(Path.cwd())


def main() -> None:
    try:
        if "--mark" in sys.argv:
            mark(hook_cwd())
        elif "--report" in sys.argv:         # Stop: only if it moved
            emit(hook_cwd(), always=False)
        else:                                # --show, the command: always
            emit(str(Path.cwd()), always=True)
    except Exception:                        # a trace must never break a turn
        pass


if __name__ == "__main__":
    main()
