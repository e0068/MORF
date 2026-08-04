#!/usr/bin/env python3
"""Builds the service views of the knowledge layer: tag dictionary and map.

TAGS.md   — tag, how many articles, where exactly. First hop of a search.
INDEX.md  — article, description, scope, applied. Second hop.

Only Facts is walked. A fact article is one that lives there; a note kept
anywhere else belongs to its owner, and the map does not reach for it.

The fact layer is the only one that never reaches the agent on its own:
observations are read at start, rules are loaded by the mechanism,
facts have to be found.
No dependencies beyond the standard library.
"""

from pathlib import Path

import morf

# ===== Settings =====

FACTS = morf.facts()
INDEX_FILE = morf.memory() / "INDEX.md"
TAGS_FILE = morf.memory() / "TAGS.md"
FIELDS = ("type", "description", "tags", "scope", "applied")
TAG_FILES_SHOWN = 12


# ===== Path check =====

def repeated_names(relative: Path, root: str) -> str:
    """A folder name states its relation to the parent, not a standalone label.

    `Facts/Cache/Cache` would read as "cache of cache", which is not a thing,
    so the level is spurious. The check: read the path bottom-up as a phrase;
    a repeated name means the phrase does not hold together. The walked folder
    is part of the phrase, so `Facts/Facts` is caught too.
    """
    parts = [p.casefold() for p in (root, *relative.parts[:-1])]
    seen, repeats = set(), []
    for part in parts:
        if part in seen:
            repeats.append(part)
        seen.add(part)
    return ", ".join(repeats)


# ===== Reading an article =====

def parse_frontmatter(path: Path) -> dict[str, str]:
    """Returns a flat dict of the YAML block at the top of the file."""
    fields: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return fields
    if not lines or lines[0].strip() != "---":
        return fields
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep and key.strip() in FIELDS:
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def listed(raw: str) -> list[str]:
    """Turns values like [a, b] or a into a list."""
    return [v.strip().strip("\"'") for v in raw.strip("[]").split(",") if v.strip()]


# ===== Walking the articles =====

def walk(facts: Path) -> tuple[list[tuple[str, dict[str, str]]], list[str]]:
    """Relative path to fields for every article, plus paths that do not read."""
    notes, suspect = [], []
    for path in sorted(facts.rglob("*.md")):
        relative = path.relative_to(facts)
        rel = relative.as_posix()
        repeats = repeated_names(relative, facts.name)
        if repeats:
            suspect.append(f"{facts.name}/{rel} — repeats: {repeats}")
        notes.append((rel, parse_frontmatter(path)))
    return notes, suspect


def clashes(notes: list) -> list[str]:
    """Articles that link as the same name: one of them becomes unreachable.

    A link is written by name, not by path — a path would resolve against the
    editor's own root, which is above us and not ours to assume. The price is
    that two files named alike in different subfolders are one link.
    """
    by_name: dict[str, list[str]] = {}
    for rel, _ in notes:
        by_name.setdefault(Path(rel).stem, []).append(rel)
    return [f"[[{name}]] is written by: {', '.join(files)}"
            for name, files in sorted(by_name.items()) if len(files) > 1]


# ===== Rendering =====

def tag_index(notes: list) -> dict[str, list[str]]:
    """Tag to the articles that carry it."""
    index: dict[str, list[str]] = {}
    for rel, fields in notes:
        for tag in listed(fields.get("tags", "")):
            index.setdefault(tag, []).append(rel)
    return index


def render_tags(notes: list) -> str:
    """The dictionary is closed: a tag missing here does not exist."""
    index = tag_index(notes)

    out = [
        "# Tag dictionary",
        "",
        "Read this before INDEX.md: it tells which part of the map to open.",
        "A tag missing here does not exist. Propose adding one; never invent.",
        "",
        "| Tag | Articles | Where |",
        "|---|---|---|",
    ]
    for tag, files in sorted(index.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        shown = ", ".join(f"[[{Path(f).stem}]]" for f in sorted(files)[:TAG_FILES_SHOWN])
        tail = " …" if len(files) > TAG_FILES_SHOWN else ""
        out.append(f"| {tag} | {len(files)} | {shown}{tail} |")
    return "\n".join(out) + "\n"


def render_index(notes: list) -> str:
    """Map of articles: the description decides whether the agent opens a file."""
    out = [
        "# Fact map",
        "",
        "Generated automatically; editing by hand is pointless.",
        f"Articles: {len(notes)}.",
        "",
        "| Article | Description | scope | applied |",
        "|---|---|---|---|",
    ]
    for rel, f in notes:
        scope = ", ".join(listed(f.get("scope", ""))) or "general"
        out.append(
            f"| [[{Path(rel).stem}]] | {f.get('description', '—')} | {scope} | {f.get('applied', '0')} |"
        )
    return "\n".join(out) + "\n"


# ===== Entry point =====

def main() -> None:
    notes, suspect = walk(FACTS)
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(render_index(notes), encoding="utf-8")
    TAGS_FILE.write_text(render_tags(notes), encoding="utf-8")

    lonely = sorted(tag for tag, files in tag_index(notes).items() if len(files) == 1)
    no_desc = sum(1 for _, f in notes if not f.get("description"))
    no_tags = sum(1 for _, f in notes if not listed(f.get("tags", "")))
    print(f"Articles: {len(notes)}. Without description: {no_desc}, without tags: {no_tags}.")
    if lonely:
        print(f"  tags on a single article, they narrow nothing: {', '.join(lonely)}")
    for line in suspect:
        print(f"  path does not read as a phrase: {line}")
    for line in clashes(notes):
        print(f"  name taken twice, rename one: {line}")


if __name__ == "__main__":
    main()
