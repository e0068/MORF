---
type: doc
description: revision history of the rules document
tags: [morf, rules]
---

**EN** — [RU](ru/правила.changelog.md)

# Rules — revision history

A new revision is added on top, under its own heading.

---

## Revision of 2026-08-05

### Structure

The document is laid out along a rule's life: **Entrance · Inside · Exit**. Three top-level sections instead of eight; two, three and two subsections in them, with "Structure", "Accounting" and "Watching" splitting into two or three more. A heading goes to whatever gets asked about separately — addresses, the folder, counters, decay, each watching mechanism, the exit condition and the return address; the depth is uneven on purpose, because splitting where there is only one question would shelve a single paragraph.

| Was | Became |
|---|---|
| "Rules you cannot judge" — the last section, about where rules come from | "Entrance", first; the section on origin stood after the sections on death |
| three paths in: from an observation, established, derived | one — from an observation. Established rules and imported conventions you bring in yourself, bypassing the routing, and are named in a single clause; the guard against the closed loop became the argument for the single path rather than a path of its own |
| "Narrowing and death" mixed together, plus "Demotion" at the end of another section: five outcomes, two of them one event under different names | one exit: return into observations. Widening and narrowing are not outcomes but movement along the reach axis while the rule is alive, and they stand in "Structure"; "moving" is not needed as a separate entity, it *is* narrowing |
| "Track record" and "Two bundles" — neighbours at the top level | one subsection, "Accounting" |

### Reversed along the way

Two decisions of this revision were made and then undone — both reversals stay here, because a silently rewritten work table would read as if it had always been right.

| Was decided | Became |
|---|---|
| a fourth value, "one mechanism per job" | dissolved: every entity that gets consulted costs the consulting — that is speed; and duplication is the opposite of a single point of truth — that is transparency |
| the canvas is derivative, the documents rule: the work table ordered `E = (V/A) × X̄` removed from the canvas | at the entrance to facts the precedence is the reverse: the `factsIn` coefficient was drawn twice, so it is a decision, and `facts.md` is what must be brought into line. Both are right and do not conflict: the canvas was stale in one place and authoritative in another — authority here belongs not to the medium but to whichever is newer and more deliberate |

### Removed

| What | Why |
|---|---|
| the hardness axis and `E = (V / A) × X̄` | `E` existed for exactly one thing — to say "time for a hook" — so the axis and the metric fall by one decision, not two. The argument "a hook closes off the view beyond it" is needed without the axis as well: it explains why the refusal to edit over someone else's change is not that kind of hook, and it moved there |
| the counters `A`, `V`, `X̄` | `A` existed for decay in applicabilities, and a rule's rhythm is visible from the spacing between its sources — that is how `score-memory.py` already scores memory lines, and a rule needs only the scale chosen by its address. `V` fed only `E`; so did `X̄` |
| accounting inside a file outside the contour | the register `map.md` in MORF. Keeping counters in `~/.claude/CLAUDE.md` would mean a machine rewriting a file outside the contour on every handoff — and running into its own hook. Recognising rules is not lost by it: the log knows their set |
| the *against* bundle as a separate entity | the arguments against are `miss` and `inverse`, the argument for is `use`, and they are already on the rule. Separate machinery would demand its own metrics and life cycle |
| the "Established" subsection as a path in | the document is about routing inside MORF, and established rules you write yourself, bypassing it |

### Added

| What | Content |
|---|---|
| how watching begins | the document described the snapshot-and-log pair and said nothing about who creates it or when. The layer could therefore never start on its own: a rule written into a file stayed invisible to it, and nobody would notice the line being deleted. The three steps are now named, and named as the agent's work; one decision stays the owner's — which of the items already standing there are rules |
| the snapshot given its job | the document promised it would "notice drift", and drift is read from the log: nobody read the copy's content, and the `outside:` verb had no producer. The snapshot now counts the lines that moved outside the rules — the one thing the log cannot know |
| taking a file under watch twice | the snapshot is left alone: rewriting it would push its mtime above the log's, and `--seal` in a folder with no registered session compares exactly those — a re-track would make the next seal refuse. The command is idempotent and exits zero: the agent is told to track a file "if it is not watched yet", nothing else answers that question, and a check must not fail on the desired state |

| What | Content |
|---|---|
| the `MORF/Rules` layout in "Structure" and the "Watching" section | addresses and the MORF folder are described together, because they are one subject — where a rule lies; watching is separate: drift, the refusal to edit over someone else's change, the log |
| the observation counters on a rule | `hit · use · miss · inverse`, `S` and `R` from `score-memory.py`, one source list. One counting language for the whole system |
| exit thresholds as settings | `miss ≥ rulesOutByMiss` or `inverse ≥ rulesOutByInverse`, a miss and a flip carry their own coefficients: they are different events, and the second weighs more. There is no intermediate stage — a narrowed rule comes back by ordinary promotion |
| the `.snap.md` suffix on snapshots | `Rules/<project>/CLAUDE.md` is picked up as a real `CLAUDE.md` on any run with cwd inside the folder |
| `address:` in the log header | two same-named checkouts give one project key; without the field the diff would be computed against a file the copy has never seen |

### Changed

| Was | Became |
|---|---|
| `<!-- A14 V3 X̄6 for:(s:…) against:(s:…) -->` beside the rule | a line in `map.md`: `- hit:6 use:4 miss:1 [S=… R=… t=…] do not use X (s:…)`. No comment is left in the outside file at all |
| "a rule is cancelled by decision", set against an observation | a rule is not refuted: `miss` and `inverse` accumulate on it and return it to memory |
| log verbs: `added · narrowed · moved · cancelled · returned · outside` | `added · widened · narrowed · returned · outside`. Widening was absent from the vocabulary entirely; `moved` merged into `narrowed`, `cancelled` into `returned`, whose line carries the address |

### Shortened

| What | Why |
|---|---|
| the "Why not otherwise" on an observation and a rule being duplicates | it retold the "Why this way"; the argument about different life cycles is kept there as one clause. The "Why not otherwise" in "Entrance" is now about something else — why there is one path |
| the argument about a "decision" — three paragraphs | one clause in "Accounting": separate machinery for what is already counted |
| the list of `E`'s properties — five paragraphs | gone together with `E` |

No argument was shortened, only retellings and what a decision above removed. Sections inherited from the old file were checked line by line against it; "Watching" and the layout — against the previous revision of this document.
