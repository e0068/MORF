---
type: doc
description: entry point to MORF — what lives where and where to start reading
tags: [morf]
---

# MORF

**M**emory **o**f **O**bservations, **R**ules and **F**acts — three-phase memory for Claude.

The order of the letters is the priority of exits: an observation is made for the sake of a rule, and settles as a fact article only when no imperative follows from it. The flow runs the other way: observations → facts → rules.

One vault, two windows. In Claude you hand out tasks and ask questions; in a notes editor you look at the same thing yourself. There are no copies — the files are the same.

## Three categories

The whole model rests on these being **different entities with different mechanics**, and confusing them is expensive.

| | What it is | Mood | Verified by |
|---|---|---|---|
| **Observation** | what happened and was unexpected | indicative | refuted by experience |
| **Fact** | an article about a phenomenon: true, repeatable, yields no action | indicative | refuted by experience |
| **Rule** | how we act from now on | imperative | only obeyed or broken |

The link is one-way and it is the point of the construction: **memory is a queue of candidate rules**. An observation either matures into a rule, or turns out to be a fact, or decays. No outcome is silent.

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

## Where to start

**[[model|The canvas]]** — the whole construction: three phases, the foundation, every transition. Start there: the notes explain the details but do not give the overall picture.

## Sections

### [[observations]]

Intake, levels, scores, the verdict. How `/morf:handoff` reconciles what happened against what was predicted instead of filtering. Why level limits are a mechanism rather than a recommendation. The formulas for `S`, `R`, `t`, and the main thing about them: the clock runs on opportunities to apply rather than the calendar, so rarity is not punished. How the verdict works — how an imperative is attempted from a cluster of observations and what a failed attempt means.

### [[facts]]

The third exit from memory, without which the system would discard what is true. Why the signal is not a deadline but the impossibility of stating an imperative. The article, `scope` as a mark of origin rather than a second contour, access in two hops through `TAGS.md` and `INDEX.md`. The return to observations when a fact starts being applied again.

### [[rules]]

Two independent axes — reach with frequency, and hardness — and why merging them was a mistake. Addresses from `~/.claude/CLAUDE.md` to an agent definition, and why a skill is a set of rarely needed rules. Two bundles of sources, for and against, both alive: an argument is not blocked, it has an entry price. The track record, `E` as risk rather than damage. What to do about rules in areas you cannot judge yourself.

### [[foundation]]

The conversation archive and why the copy is permanent rather than a reference to Claude Code's store. The session index, which doubles as the time scale of the whole model. `/morf:why` — how to get from any line back to the conversation. The split of settings: numbers for the code, instructions for the agent. The `/morf:audit` every tenth session. And what stays outside the system: tasks.

### [[setup]]

Steps, command texts, the `CLAUDE.md` template. Nothing of the model is restated there.

## Scripts

| File | What it does |
|---|---|
| `archive-session.py` | the hook: session registration and transcript copies |
| `score-memory.py` | `S`, `R`, `t` in the memory files |
| `read-session.py` | a readable conversation from the archive, for `/morf:why` |
| `build-index.py` | `TAGS.md` and `INDEX.md` — access to the fact layer |
| `guard-archive.py` | blocks writes and deletes inside the archive |
| `config.json` | weights, scale unit, level step |

## What to know before starting

**The payoff does not come at once.** For the first weeks the levels will look like pointless work: there is little evidence, the scores do not discriminate, no rules appear. The point emerges around the third month, when the upper levels start holding what you have already forgotten. This is not a quirk of this design — over short horizons a memory architecture barely affects results at all, because the conversations are still in context.

**The system rests on `/morf:handoff`.** If it stops being called, the levels drain from the bottom up, and within a month only what recorded itself reaches memory. A cut-down daily entry beats none.

**The numbers are starting values.** `min_events`, the weights for `miss` and `inverse`, the level limits. They come from common sense rather than from your data, which does not exist yet. In a couple of months it will be clear what to change, and `/morf:audit` will show in which direction.

**One value stays a self-report.** `use` — how many times a line changed what you did. There is nothing to verify it with: applying a record happens in the work, and the work is outside the system. The sign that the agent is inflating it: the list by `R` stops differing from the full list.
