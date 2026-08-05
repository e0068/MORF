---
type: doc
description: the observation layer — intake, levels, scores, the verdict; how it works and why
tags: [morf, observations]
---

# Observations

**EN** — [RU](ru/наблюдения.md)

**What this is.** Records of something that happened and was unexpected. Indicative mood, always inside a project, always with sources.

**What for.** This is a queue of candidate rules. An agent records an observation when it runs into something the system did not contain; the counters answer not "is this worth keeping" but "has it matured enough to change behaviour".

---

## Intake: reconciliation, not filtering

**How it works.** At the end of a piece of work `/morf:handoff` runs. It takes the last row of the session index — that is the current session, and its id becomes the source — and sorts out what happened:

| What happened | What gets recorded |
|---|---|
| no opportunity arose | nothing, only an exposure tick |
| the prediction held | `hit` on an existing line |
| the line changed a decision | `use` |
| the prediction did not hold | `miss` |
| the opposite happened | `inverse` **and a new line** |
| the system did not contain this | a new line in `L0.md` |

An early conclusion — when the wording wants to be imperative — is written in the indicative, marked `↑`, with the proposed rule attached below it.

**Why this way.** An unexpected outcome means a gap in the system, and a gap is closed, not filtered out. Expected outcomes are events too, and informative ones: confirmations and refutations accumulate only here.

`hit` and `use` are separate because they measure different things: the first is correctness, the second is demand. Their divergence is `R` — the case of "everyone leans on this line, and it was verified once". Under a single counter that case is invisible.

`inverse` starts a new line because the opposite happening is itself unexpected and deserves its own record with its own sources.

The early conclusion is kept because the agent is inside the context and sees details that will never reach the record.

**Why not otherwise.** Two filters used to guard the intake; both are gone.

The cost of forgetting — "what happens if I forget this" — is a judgement call, and every judgement call has been cleared out of the system. It would also filter out the rare and important along with the useless.

Mood stopped being a filter because an observation is indicative by nature: turning it into "do not do X" requires a move from fact to decision, and that move happens later. There is nothing to check at intake. What remains is diagnostics: an imperative line means the agent reflected too early.

**The intake trusts that the transcript is independent of memory, and it is not.** A subagent reads `L1`–`L3` back into the session, its words land in the copy `/morf:handoff` reads, and read back they wear the face of a fresh event — an echo about to be recorded as an observation. So before a new line is written the thought is grepped across the levels above `L0`: a match is not something the system did not contain, it is something the system has just said. At most it is a `hit` on the line that already carries it, and only if the situation itself recurred; the echo alone earns nothing. The grep catches the literal repeat — a reworded one still rests on the reconciliation's own judgement, which no string match can stand in for.

---

## Levels and limits

**How it works.**

```
MORF/Memory/<project>/
├── L0.md      intake, never loaded into context
├── L1.md      held a second time, or changed a decision
├── L2.md      changes behaviour in tasks that do not exist yet
├── L3.md      lived out its horizon without refutation
└── dropped.md displaced, no limit
```

Promotion is possible only if the weakest line by `S` leaves the level. What is displaced moves to `dropped.md` whole.

Horizons and limits are not baked into the names: they are computed from `config.json` and published in `levels.md`, which the agent reads.

```json
"unit": "sessions",      scale: sessions or days
"horizon_base": 1,       horizon of the first level
"horizon_step": 5,       how much the next one grows
"limits": [40, 30, 25, 20]
```

At step 5 the horizons come out as 1 · 5 · 25 · 125 sessions; on the calendar with step 7 that is 1 · 7 · 49 · 343 days, roughly a day, a week, six weeks and a year.

**Consolidation runs top down:** `L2` is filled from `L1` first, then `L1` from `L0`. Bottom up a line would climb two levels in one pass, and each level is meant to be a separate check.

**Why this way.** The limit forces a comparison: for something to rise, something has to leave. Levels only decide what is stored; the position of a line does not affect its exit — that is computed from its score, not from its floor.

**Why the scale is a choice.** Calendar and sessions measure different things, and which is right depends on how you work. Ten sessions in a day and ten in a month give the same material for consolidation, and the calendar cannot tell them apart. But some observations do go stale by the calendar: a dependency version, the composition of a team, an agreement for the quarter. There is no right answer in advance, so it is a setting rather than the author's decision.

Under the session scale the level names stop meaning a literal span: `L1` is "the second level", not "a week". The exact horizon is always visible in `levels.md`.

**Why not otherwise.** The first version made limits a recommendation, and within a month the levels became identical lists with different names: the top one weighed as much as the bottom one, and the split lost its meaning.

The same version split observations into two pools, project and general, with a move across on confirmation in a second project. That strangled accumulation: one conclusion drawn in projects A and B became two lines with `hit:1` in different folders, neither gathered weight, and nobody ever moved them by hand. Generality belongs to the rule derived from an observation, not to the observation.

---

## Line format

**How it works.**

```markdown
- hit:3 use:7 miss:1 inverse:2 [S=2.4 R=3.0 t=1.2] text (s:260731-9c2e#12-88)
<!-- moves: s:260901-aa11 fact, s:261102-bb22 observation -->
```

Zero counters are omitted. The scores in square brackets are written by the script. The comment holding the move history is stripped before the context, so it costs nothing.

A source points not only at a session but at a stretch inside it: `s:260803-a41f#412-980`. The line numbers come from `archive-session.py --handoff` — at that moment the copy ends exactly where the piece of work ended.

**Why this way.** A line without sources is invalid and is discarded during consolidation: `/morf:why`, the time scale and the very possibility of disputing a record all rest on sources.

A stretch rather than a whole session is needed because `/morf:handoff` runs several times per session. Without it every line of a session would point to the same place, and `/morf:why` would open a six-hour conversation instead of the ten turns that matter.

Counters are named with words. The previous `×` and `✗` are indistinguishable in most fonts while meaning the opposite; `∅` renders as `ø`. The shapes were also inconsistent — four different sign families for four values on one scale.

**Why not otherwise.** Sources could be trimmed during consolidation for compactness. Then consolidation would lose not only the text but the link to the conversations — and that link is the only thing that makes the construction verifiable.

---

## Scores

**How it works.** `score-memory.py` computes them, reading the weights from `config.json`. The age of an event is how many sessions of the project have passed since.

```
s = e₁ · N / e_N                          overdue
Neff = N · min(1, 1/s)                    for each kind of event
C = 1 − 2^−(hit − miss·wm − inverse·wi)   confidence, never below zero
S = C + ln(1 + use)                       maturity of the candidate
R = use × (1 − C)                         urgency of verification
t = r₂ / r₅                               direction
```

**Why this way.** The clock runs on opportunities to apply: an observation about release builds applies once a month, one about code style hourly, and on the calendar the first would always look stale. The calendar punishes rarity, not incorrectness.

Decay is derived from the record itself: its rhythm `e_N/N` sets the schedule, and the overdue shows how many times over it is late against that rhythm. At `s ≤ 1` there is no discount at all.

The logarithm on `use` reflects diminishing returns: the tenth reference says almost as much as the third.

`inverse` weighs twice as much as `miss` because the opposite is observable while a non-event is only an absence.

`S` is a sum, not a product. Multiplied, a record that everyone leans on and nobody verified would get zero and fly out — the system would discard exactly what it meant to check.

The script counts, not the agent, because counting is the task where an agent quietly nudges the result towards what it would like to keep.

**Why not otherwise.** Every tuned parameter is gone from the model: half-life, decay coefficient, the choice between a week and a month. What remains is `min_events = 3`, meaning "this record is still immature".

A fixed window of the last `N` opportunities came out empty for a rare record and returned zero where the right answer was "rare but reliable".

A formula built on inter-event gaps, `Σ 1/(N·gₙ)`, confused the cases: the weight depended on the ordinal number of an event rather than its recency, so a dense old cluster outranked a record still in use.

A hybrid with a calendar ceiling would solve the problem of an observation living forever in an abandoned project — but such a project is simply never opened, and its memory affects nothing. The price of a hybrid is two scales to reconcile at every boundary between entities.

**The check after any edit.** On a scale of 60 sessions "often and recently" and "rarely but reliably" give the same `S` = 2.82. If they diverge, the calendar has crept back in.

---

## The verdict

**How it works.** It reads lines from any level and routes them to three exits.

1. It gathers close lines into a cluster. Three observations about the cache from different angles make one rule; separately none of them carries. Weight is counted per cluster, sources are taken from all of them.
2. It tries to state an imperative.

| Result of the attempt | Exit |
|---|---|
| stated, weight suffices, already tried against what happened | rule |
| stated, weight too low | stays on its level |
| cannot be stated at all | fact |
| weight decayed | `dropped.md` |

A rule is only created after the candidate has been run at least once against what already happened: against recent diffs, against build logs, against anything. Who ran it — a subagent tester, a code reviewer, or the agent itself — does not matter to the system; the fact of the run does.

Two phases: 🟩 at the end of a session, inside the task, the wording is formed; 🟦 at the start of the next one, without a task, the decision is made.

**Why this way.** The check runs at any level because maturing is not the same as climbing: levels are about storage, the verdict is about release. They are linked only through `S`, which is higher for a long-lived line.

The phases are split by context, not by executor. Wording benefits from the agent being inside the task and seeing the details; the decision suffers from it — from inside a fresh successful case the weight of evidence cannot be judged, because that case weighs more than all the others simply by being in view.

An imperative produced by prefixing "do not" to an observation is a restatement. A real rule adds what the observation lacks: what to do instead, under which condition. If nothing was added, the observation has not matured as content rather than as weight.

The verdict is a mechanism, not a role: whoever is working performs it. Memory must not depend on whether development is under way.

**Why not otherwise.** An early version made maturing the top level — a `ready.md` file a line reached after a year. That is a spurious intermediate store: maturing is a state, not a place, and it can happen at any level.

The same version tied the verdict to the orchestrator. The orchestrator is about development, while memory is needed where there is none: in a chat, in a one-off session, in a task that has nothing to do with code.

There is no separate consolidation command: it would be one more ritual, and rituals are the first thing to lapse. Consolidation runs at session start when enough has accumulated. One exception: an `inverse` on a rule suspends it immediately — a confirmation can wait, an error cannot.

---

## What is displaced

**How it works.** `dropped.md` grows without a limit and nothing is ever deleted from it. A line moves there whole: counters, sources, move history. `/morf:why` still works on it.

**Why this way.** The decision is reversible, and reversibly for real: from a displaced line you can raise the conversations it came from and understand why it was thrown out.

**Why not otherwise.** An automatic return was considered: on writing a new observation, look for a similar one in `dropped.md` and revive it with its old counters.

Rejected for five reasons. Matching by meaning is non-deterministic — a wobbly step would appear where everything else is counted. Reading a growing file on every write is expensive. Revived counters lie: `use` would come back in full. The mechanism would turn `dropped` into one more level, only an endless one. And above all, it would treat the symptoms of a threshold set too low and thereby hide that the threshold is wrong.

Instead there is `/morf:audit` from [[foundation|the foundation]]: it shows whether the problem exists and decides nothing.
