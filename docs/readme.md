---
type: doc
description: entry point to MORF — what lives where and where to start reading
tags: [morf]
---

# MORF

**EN** — [RU](ru/начало.md)

**M**emory **o**f **O**bservations, **R**ules and **F**acts — three-phase memory for Claude.

At the end of a piece of work the agent records what happened and was unexpected. Those observations accumulate, get scored and are consolidated level by level. What matures into "do it this way" becomes a rule; what stays true but yields no action settles as an article about the phenomenon; what stops being confirmed and used is displaced with its sources intact.

One folder, two windows. In Claude you hand out tasks and ask questions; in a notes editor you look at the same thing yourself. There are no copies — the files are the same.

## Three categories

The whole model rests on these being **different entities with different mechanics**, and confusing them is expensive.

| | What it is | Mood | Verified by | Access |
|---|---|---|---|---|
| **Observation** | what happened and was unexpected | indicative | refuted by experience | fast: read at session start |
| **Fact** | an article about a phenomenon: true, repeatable, yields no action | indicative | refuted by experience | slow: found by search |
| **Rule** | how we act from now on | imperative | only obeyed or broken | fast: loaded by the mechanism |

The access column explains a lot of the design. Observations and rules arrive on their own, so they are kept under hard limits: the context is finite and everything loaded costs something every session. Facts are loaded by nobody until somebody looks for them, so they may be any number — and that is exactly why the fact layer needs two indexes while the other two need none.

The link is one-way and it is the point of the construction: **memory is a queue of candidate rules**. An observation either matures into a rule, or turns out to be a fact, or decays. No outcome is silent.

## Three axes

Each axis pairs up two of the three, and no pair repeats.

| Axis | Observations | Facts | Rules |
|---|---|---|---|
| **Mood** | indicative | indicative | imperative |
| **Access** | fast | slow | fast |
| **Persistence** | transient | persistent | persistent |

Observations and facts meet on mood, observations and rules on access, facts
and rules on persistence. Every pair shares exactly one axis, and no two
entities match on all three.

The axes are not decoration: each one drives a mechanism. Mood is what the
intake filter checks. Access decides who needs indexes — only the slow layer
does. Persistence decides who decays: an observation exists to be
resolved into a rule, a fact or `dropped`, and stops existing once it is, while
a fact and a rule are outcomes that stand until disproven.

## Who does what

On the canvas the colour of an arrow marks the executor. The distinction matters: the same steps are done by different agents precisely because their context and their stake differ.

| | Executor | What it does |
|---|---|---|
| 🟩 | agent inside a task | works, notices the unexpected, runs `/morf:handoff`, drafts a candidate rule |
| 🟦 | agent at session start | consolidates the levels and decides what the verdict releases |
| 🟪 | reviewer | runs a candidate against recent diffs |
| 🟥 | you | one transition only — into enforcement |
| ⬜ | scripts and hooks | archive, scores, indexes; no interpretation |

Green and blue are **the same mechanism in different context**. Wording benefits from the agent being inside the task and seeing details; the decision suffers from it — from inside a fresh successful case the weight of evidence cannot be judged, because that case weighs more than the rest simply by being in view.

## Values

Three, and every "why this way" in these notes reduces to one of them.

**Evolvability.** The system must survive its own mistakes without losing what it accumulated. So nothing here is deleted: what is displaced goes to `dropped` with its sources, a refutation narrows a rule rather than cancelling it, a withdrawn rule returns to memory with its history, and the transitions are recorded in `moves`. A decision you cannot learn has already failed will be made again in six months.

**Speed.** Everything that loads by itself costs tokens in every session; everything hanging on a hook costs time on every turn; and every entity created costs the consulting it will take. Hence the hard level limits, the transition history riding on the record as one `moves` comment line rather than a journal of its own, facts that nobody loads until they are searched for, scripts without a single dependency — and the refusal to create a second mechanism where an existing one copes: a repeat raises a counter rather than breeding a record, a skill is not an entity but an address on the reach axis, there is no *against* bundle because `miss` and `inverse` are already counted.

**Transparency and reliability.** One point of truth, and nothing breaks silently. Hence **encapsulation**: MORF writes only inside its own directory, and carries outward exactly one thing — the rule's text, without which it would not load. Hence a source on every line, an archive that never expires, `/why` down to the raw conversation, obligations derived from what already lies on disk — and the refusal of a duplicate in any form: justifying a rule in prose would be a third copy, a second file holding the project's path would go stale on the first move, a separate transition journal would have to be tied to the records. Hence two further refusals: not to count what cannot be checked, and not to decide for you where there is no right answer in advance — the scale unit and the language stay settings, and adopting an older line of your own stays your call — never one the system raises. Names belong here too: a path and a title must hold their meaning, because a name that stops holding it hides what the thing is.

## Where to start

**[[model|The canvas]]** — the whole construction: three phases, the foundation, every transition. Start there: the notes explain the details but do not give the overall picture.

## Sections

### [[observations]]

Intake, levels, scores, the verdict. How `/morf:handoff` reconciles what happened against what was predicted instead of filtering. Why level limits are a mechanism rather than a recommendation. The formulas for `S`, `R`, `t`, and the main thing about them: the clock runs on opportunities to apply rather than the calendar, so rarity is not punished. How the verdict works — how an imperative is attempted from a cluster of observations and what a failed attempt means.

### [[facts]]

The third exit from memory, without which the system would discard what is true. Why the signal is not a deadline but the impossibility of stating an imperative. The article, `scope` as a mark of origin rather than a second contour, access in two hops through `TAGS.md` and `INDEX.md`. The return to observations when a fact starts being applied again.

### [[rules]]

One entrance and one exit, both through memory: a rule is derived from a mature observation and returns to observations when it errs. Addresses from `~/.claude/CLAUDE.md` to an agent definition, and why a skill is a set of rarely needed rules. The same counters an observation carries, kept in MORF rather than in the file the rule lies in — and the snapshot and log that notice when that file changes without us.

### [[foundation]]

The conversation archive and why the copy is permanent rather than a reference to Claude Code's store. The session index, which doubles as the time scale of the whole model. `/morf:why` — how to get from any line back to the conversation. The split of settings: numbers for the code, instructions for the agent. The `/morf:audit` every tenth session. And what stays outside the system: tasks.

### [[setup]]

Steps, command texts, the `CLAUDE.md` template. Nothing of the model is restated there.

## Scripts

| File | What it does |
|---|---|
| `archive-session.py` | the hook: session registration, shelves, transcript copies |
| `due.py` | what the memory owes, on every turn and at the end of one |
| `score-memory.py` | `S`, `R`, `t` in the memory files, and `levels.md` |
| `read-session.py` | a readable conversation from the archive, for `/morf:why` |
| `build-index.py` | `TAGS.md` and `INDEX.md` — access to the fact layer |
| `guard-archive.py` | blocks writes and deletes inside the archive |
| `rules.py` | the register, the snapshots and what changed in a watched file |
| `guard-rules.py` | keeps a watched file from drifting away from its record |
| `morf.py` | where the MORF folder is; imported by the rest |
| `config.json` | weights, scale unit, level step, the rule thresholds |

## What to know before starting

**The payoff does not come at once.** For the first weeks the levels will look like pointless work: there is little evidence, the scores do not discriminate, no rules appear. The point emerges around the third month, when the upper levels start holding what you have already forgotten. This is not a quirk of this design — over short horizons a memory architecture barely affects results at all, because the conversations are still in context.

**The system rests on `/morf:handoff`.** If it stops being called, the levels drain from the bottom up, and within a month only what recorded itself reaches memory. A cut-down daily entry beats none.

**The numbers are starting values.** `min_events`, the weights for `miss` and `inverse`, the level limits. They come from common sense rather than from your data, which does not exist yet. In a couple of months it will be clear what to change, and `/morf:audit` will show in which direction.

**One value stays a self-report.** `use` — how many times a line changed what you did. There is nothing to verify it with: applying a record happens in the work, and the work is outside the system. The sign that the agent is inflating it: the list by `R` stops differing from the full list.
