---
type: doc
description: the rule layer — one entrance, reach, the observation counters, the register and its history, one exit
tags: [morf, rules]
---

**EN** — [RU](ru/правила.md)

# Rules

**What this is.** Instructions on how to act. Imperative mood, applied anywhere. They are never true or false — only obeyed or broken; the consequences of applying a rule do not refute it, they return it to observations.

**What for.** One of memory's three outcomes, and the only one that changes what you do. A fact changes your bearings — true, repeatable, produces no action; `dropped` closes the case of "did not hold up". None of the three is lesser than the others, they do different work.

**What it consists of and where it lies.**

1. The text — a list item in the imperative. That is all that lies in a file outside the MORF contour.
2. The accounting — a line in the register `MORF/Rules/map.md`: the same counters a memory line carries, the `S` and `R` computed from them, and the source list — see "Accounting".
3. The rule lies in one of the five files outside the contour, at an address from "Structure"; the file is its contour: in another project the rule is not hidden, it does not exist.
4. On that file MORF keeps a snapshot `*.snap.md` and a log `*.log.md` — see "Structure" and "Watching".

---

## Entrance

### Out of observations

**How it works.** There is one path, and it runs through memory. A rule is never written directly: the line lives as an observation, gathers `hit` and `use`, rises through the levels, and at consolidation an imperative is attempted from it. It follows — the line leaves for an address from "Structure" and counts as a rule from then on; it does not — the line stays an observation or settles as a fact.

The content decides which door the line leaves by: "do it this way" follows — a rule; it cannot follow in principle — a fact (see [[facts]], and the threshold of that door is there too). This door has two conditions, both required:

```
S ≥ rulesInScore        maturity
use / hit ≥ rulesIn     applicability
```

**Maturity** is checked as it is everywhere in the system: from the score, not from the level the line sits on (see [[observations]]).

**Applicability** is not a share: `use` is not a subset of `hit`, and the ratio freely exceeds one — the example in [[observations]] reads `hit:3 use:7`. It is a rate: how many applications there are per confirmation. `hit` is the denominator, so the door demands at least one confirmation — at `hit:0` the condition fails for any `use`.

**Why two and not one.** `S` is itself assembled from the same counters — `confidence(hit, miss, inverse) + log1p(use)` — but at `use:0` the second term vanishes, and a line with high `confidence` clears the `S` threshold having changed nothing. It is true and useless as an instruction: its place is in facts, not in `CLAUDE.md`. The first check does not see this; the second measures applicability as such, not only its absence.

Both coefficients live in `config.json`. There is no right value in advance: it depends on how fast material accumulates and how much a mistake costs — so it is a setting, not a postulate.

**Why this way.** "X breaks the build under Y" and "do not use X" are different statements. An indicative wording forces you to name what was actually observed: "do not use X" hides the grounds, "X breaks the build under Y" presents them and is therefore usable by `/why`. So memory holds the observation and the imperative is derived from it — not the other way round.

**Why not otherwise.** Writing an imperative directly would be a second door, and through it a rule would arrive with no counters, no sources and no standing: `/why` would reach nowhere, and there would be nothing to compute `S` from. It also closes the loop in which the agent proposes a rule and then confirms it itself.

### What the routing does not cover

**How it works.** Design, process, who reviews what, the published conventions of a language and the linter defaults — all of that you bring in yourself. So do grounds from outside the observation contour: deadlines, someone else's priorities, someone's will. A weighty ground arrives as your instruction, not as a conclusion drawn from memory, and does not go through the entrance.

**Why not otherwise.** A second path — "the agent invented a rule from general considerations" — is deliberately absent: it closes the loop in which the agent proposes and confirms by itself, and in half a year `CLAUDE.md` consists of well-sounding platitudes. You cannot check the content, so the entrance must.

---

## Inside

Address and layout, counters, watching.

### Structure

#### Addresses

**How it works.** The address decides when a rule reaches the context.

| Address | When it loads |
|---|---|
| `~/.claude/CLAUDE.md` | always, in every project |
| `CLAUDE.md` of the project | always in this project |
| `.claude/rules/` with `paths:` | when working with those files |
| `SKILL.md` | by the meaning of the task |
| an agent definition | when that role is invoked |

The contour is a file: in another project a rule from that project's `CLAUDE.md` is not hidden, it physically does not exist.

While a rule is alive it **moves** along this axis, and both movements go into the log:

- **widening** (`widened`) — confirmed in a second project, the rule travels wider;
- **narrowing** (`narrowed`) — either `do not X` → `do not X when Y`, or the same move but narrower: into an agent definition, into a skill, into `.claude/rules/` under `paths:`. It is one operation: narrowing the condition and narrowing the address are two ways of shrinking the area of application, and a falling frequency leads to the same place.

The line is not created anew when it moves: counters, sources and move history stay with it, the address or the wording changes. Movement is not an exit from the layer — there is one exit, and it is in "Exit".

**Why this way.** These are addresses, not steps: there is no summit, wider is not better than narrower, and movement goes both ways along one and the same axis. `CLAUDE.md` loads always, so only the frequent belongs there, and the rare is displaced into a skill or an agent definition. Hence the explanation of where skills come from: **a skill is a set of rarely needed rules, loaded by the meaning of the task.** Not a separate entity, but an address on the same axis.

#### The folder

**How it works.** All five addresses lie outside MORF, so for every watched file MORF keeps a pair: a snapshot `*.snap.md` — the file as it stood when its rules were last accounted for — and a log `*.log.md`, written by hand, saying what became of them.

```
MORF/Rules/
├── map.md                      the register: a line per rule, counters and sources
├── home/                       everything under `~/.claude`
│   ├── CLAUDE.snap.md · CLAUDE.log.md
│   ├── Agents/code-reviewer.snap.md · code-reviewer.log.md
│   └── Skills/morf/SKILL.snap.md · SKILL.log.md
└── <project>/
    ├── CLAUDE.snap.md · CLAUDE.log.md
    ├── Paths/api.snap.md · api.log.md      ← `.claude/rules/` with `paths:`
    ├── Agents/qa.snap.md · qa.log.md
    └── Skills/deploy/SKILL.snap.md · SKILL.log.md
```

Watched files are the ones MORF wrote to itself, plus those taken by hand; the presence of a snapshot is the mark of watching. The register is one for everything: `map.md`, a section per file, a line per rule — see "Accounting".

Watching begins at the moment a rule is put there, and the agent begins it, not you: write the text, take the file under watch if it is not already, enter the rule in the register and in the log. All three steps are its work. Your role in this layer is the one you have in the whole system: to approve a hook.

One decision is still yours, because the machine cannot make it. Items already standing in a watched file are shown as candidates, and the question put to you is not which of them are imperatives — most will be. It is which ones MORF starts accounting for: counting them, noticing an edit, missing them when they go. An item left unadopted keeps working exactly as before; this layer simply does not answer for it.

Taking a file under watch a second time is refused. It would overwrite the snapshot and seal a foreign change nobody has accounted for — and sealing must be a deliberate act, with a command of its own.

**Why this way.** The top level of the folder is the root a file hangs off, not its reach: reach is derived from the address and written in the header of the `map.md` section. Otherwise a skill from `~/.claude/skills/` would land in a folder named "everywhere", though it loads the most rarely of all. `.claude/rules/` is called `Paths` — `Rules/<project>/Rules` would repeat the name and stop reading as a phrase.

Every snapshot carries the `.snap` suffix, though it exposes only one case: `Rules/<project>/CLAUDE.md` is a valid `CLAUDE.md` for any run with cwd inside that folder, and it would be picked up as the real one. The naming rule must not depend on which of the five addresses a file came from, so both ends of the pair are marked.

**Why not otherwise.** A version per edit is git inside memory: the folder grows along with every typo. History lives in the log, where it has verbs and sources. The snapshot is left with one job the log cannot do: drift is read from the log, because the log knows what the file should hold — but how much else moved in the file is known only to the previous copy. That is the count in an `outside:` entry. Nor is the project's path kept on disk: the root is cwd, and a second source of truth about where the project lies goes stale on the first move.

### Accounting

#### Counters

**How it works.** The accounting lies in MORF, not in a file outside the contour: the register `MORF/Rules/map.md`, a line per rule, in the shape of a memory line. The counters are the same, and the same `score-memory.py` computes them.

```markdown
## ~/.claude/CLAUDE.md — home, always

- hit:6 use:4 miss:1 [S=1.8 R=0.4 t=1.2] do not use X in release builds (s:260731-c19d, s:260805-a41f)
- hit:2 use:1 [S=0.9 R=0.5 t=0] do not commit generated files (s:260802-7f31)
```

- `use` — the rule changed a decision: an argument **for**;
- `miss` — it did not work as promised, `inverse` — the opposite happened: arguments **against**, and `inverse` weighs twice as much;
- `hit` — the rule's prediction held;
- `S` — strength: for an observation it is maturity as a rule candidate, for a rule it reads as "worth keeping"; `R` — that it is due for a check; `t` — where the tempo is heading, and it is zero until there are five events.

**Why this way.** One counting language for the whole system. A rule came out of an observation and goes on living by its counters: nothing new has to be created, `/why` reaches the raw conversations from a rule through the same source list, and `score-memory.py` parses this line with the same expression it parses a level line with.

The accounting is in MORF and not outside because a file outside the contour is not ours: writing into it on every handoff would mean a machine rewriting `~/.claude/CLAUDE.md` for the sake of numbers only we need. What stays in that file is exactly what it is there for — the imperative.

**Why not otherwise.** A marker in the file outside the contour is not needed: the set of its rules is derived from the log, which writes `added:` for every rule put there and `returned:` when one leaves. An item the log does not know is not a rule.

Justifying a rule in prose is unnecessary: there are counters, sources and `/why` down to the conversations. A retelling would be a third copy — unverifiable and going stale silently.

A separate *against* bundle — the observations that lost when the rule was made — is not created: the arguments against are `miss` and `inverse`, the argument for is `use`, and all of it is already on the rule itself. Separate machinery would demand its own metrics and its own life cycle for what is already counted.

A damage counter is rejected: almost always zero, it creates the impression that the absence of losses says something, and it demands a self-report from the agent. A three-level cost scale is rejected too: the single place in the whole construction where someone judges rather than counts.

#### Decay

**How it works.** A rule's rhythm is visible from the spacing between its own sources, and **the address chooses the scale**: a rule from `~/.claude` loads in every session, so its clock is the whole session index; a rule in a project file is counted by that project's sessions.

**Why this way.** Decay must be counted in applicabilities: a release rule applies once a month, a code-style rule hourly, and extinguishing them at the same pace makes no sense. Since the rhythm is read from the sources themselves, no separate opportunity counter is needed after that.

**Why not otherwise.** The scale cannot always be the project's. A rule from `~/.claude` has no project, its sources come from several, and on a project scale not one of them would resolve: an empty scale means no decay at all, so the widest rules would have no exit whatsoever. The error would also run the wrong way — the more projects a rule proved itself in, the less it could ever decay.

### Watching

The rule's text stands in a file anyone may rewrite, and its disappearance would go unnoticed. Watching is drift, refusal and record: comparing the file with what MORF knows about it, refusing to edit over someone else's change, and the log where all of it lands.

#### Drift

**How it works.** What is compared is rule text: what the log knows about the file against what stands in the file. Drift is a rule gone, changed, or an item appearing where the log does not know it. Counters do not enter the comparison at all: they lie in the register, in MORF, and a file outside the contour does not carry them. Drift is a memory debt like consolidation and the audit, and it arrives by the same rules.

```
rules: CLAUDE.md changed and 2 rule(s) are unaccounted — run rules.py --diff
rules: ~/.claude/CLAUDE.md is gone while MORF still watches it
```

**Why this way.** Counters and `[S= R= t=]` move on every handoff, and were they to lie in a file outside the contour the debt would arrive on every turn, while the machine's own edit of the numbers would run into its own hook. In MORF they create neither, and the machine does not touch the outside file at all.

The comparison runs against the log, not against a list marker. These files hold imperatives of two origins: the ones that came out of memory, and the ones you wrote yourself — design, process, conventions, everything the routing does not cover. By shape they are indistinguishable: in `SKILL.md` the items are instructions throughout, the `CLAUDE.md` template consists entirely of items, and the `<!-- morf:language -->` block is rewritten by the installer on every reinstall. Only the log tells them apart: it knows exactly the items MORF put there, and those are exactly the ones MORF answers for.

**Why not otherwise.** A rule added to the file by hand is unknown to the log, and it does count as drift — but not as a debt, as a candidate: a line saying "the file has an item the register does not", with an offer to take it under accounting. Telling an added rule from added prose inside a file outside the contour is impossible, so a human decides, not the machine.

#### No editing over someone else's change

**How it works.** The hook does not let through an edit of a watched file that carries **someone else's** drift, and puts those very rules on stderr:

```
Blocked: CLAUDE.md changed outside MORF and 1 rule(s) are unaccounted.
  − do not use X in release builds
  + do not use X in release builds when Y
Write them into the log, run rules.py --seal, then repeat the edit.
```

Someone else's is whatever was already drifted at the start of the session.

**Why this way.** The debt catches drift but not the worst case: the rules were changed outside MORF and the agent is adding to the same file — the edits mix, and telling whose is whose becomes impossible. The diff is needed exactly at the moment the agent is about to write. "At the start of the session" — otherwise it would block itself with a diff of its own work from one turn ago.

A hook is a hard constraint imposed from outside: it closes off not only the violation but the view beyond it, and a bad hook is indistinguishable from a perfectly working rule. So exactly one move is closed — writing over someone else's unaccounted change — and it opens with a log entry, the very action the folder exists for. The view is not closed: the diff is shown in full.

**Why not otherwise.** Two boundaries are named rather than hidden: your edits made mid-session land in the list at the next start, and yesterday's session continued today arrives with a different slug, so an unsealed drift comes back to the agent as someone else's. A broken import opens the way through: the hook guards the accounting, not the evidence.

#### The log

```markdown
---
name: MORF-CLAUDE.md-log
address: /Users/e0068/dev/MORF/CLAUDE.md
---

## s:260805-a41f

- added: do not use X in release builds (s:260805-a41f#412-980)
- widened: do not use X → @~/.claude/CLAUDE.md (s:…) — held in a second project
- narrowed: do not use X → do not use X when Y (s:…) — miss
- narrowed: do not X → @Skills/morf/SKILL.md (s:…) — too rare for CLAUDE.md
- returned: do not commit generated files → @L0 (s:…) — as it stood, S decayed
- returned: do not Y → @L0 (s:…) — with inverse:+1, the opposite was observed
- outside: 12 line(s) changed (by hand) — no rule touched
```

Five verbs. `added` — the rule arrived from memory; `widened` and `narrowed` — movement along the reach axis while it is alive; `returned` — the exit back into observations, and its line says where the line moved and what was appended to it; `outside` — an edit that touched no rule. Every line carries a source reference or an explicit `(by hand)`; without either the line is invalid, as a memory line would be. The source closes the entry: whatever follows it is prose for a human, and nothing before it is. No character separates the reason inside the entry, because every candidate — an em dash, brackets — occurs in rule texts and would truncate them. The log is never deleted: a file may stop being watched, the history stays. `address:` in the header is the real path of the watched file: two same-named checkouts give one project key, and without that field the diff would be computed against a file this copy has never seen.

To the right of `→` stands either a new wording or an address — and an address always carries `@`. Telling them apart is not only the reader's problem: the set of a file's rules is derived from the log, so `narrowed: A → B` and `narrowed: A → @B` mean different things, and the sign decides which. A move requires the receiving file to be watched as well, otherwise the trail loses half of itself; what links the two entries is a shared source reference.

`--seal` clears one file's entry from the list: clearing the whole of it would unblock everything else that drifts and that nobody has described. And it refuses when the log has no entry for the current session — describe first, then seal. Where no session is registered, `--seal` says so and proceeds, otherwise the folder would never seal and the hook would become permanent; the promise in that bypass is held by a check that needs no identifier: the log must be newer than the snapshot.

---

## Exit

There is one exit: back into observations. Widening and narrowing are not exits — they are movement along the reach axis while the rule is alive, and they are described in "Structure".

### When

**How it works.** A rule leaves the layer when any of these fires:

```
miss    ≥ rulesOutByMiss
inverse ≥ rulesOutByInverse
```

plus a third: `S` has decayed — the rule stopped applying, and nothing new was observed in the process.

The third has no coefficient, and it is the only one of the three exits that is noticed at consolidation rather than counted. There is nothing to count: decay has no event, it *is* the absence of events. The asymmetry is said out loud, because `score-memory.py` rests on "the script counts, not the agent: otherwise the numbers get nudged", and one exit left to the eye is an exception to that rule, not its absence.

A miss and a flip have their own coefficients because they are different events: `miss` says "it did not work as promised", `inverse` says "the exact opposite happened". The second weighs more, and its threshold is usually lower.

**Why this way.** By default one is enough for either: waiting for a majority means working on knowingly false grounds for several more sessions, and that costs more than running the line through memory once more. The setting is needed because the price of a mistake differs, and the threshold is raised where a rule twitches at noise.

There is no intermediate stage. A rule that erred returns to observations whole — and if it has the evidence for it, it comes back narrowed, by ordinary promotion. The loop is exactly one consolidation longer, but it runs on the same mechanism rather than its own.

### Where

**How it works.** The rule is not deleted and not written anew: the line **moves** out of the register into `L0` with its counters, its sources and its move history. The `[S= R= t=]` block is stripped on the way: it is not history but computed from it, and consolidation restores it when the line rises to a level. If the rule was refuted, `inverse:+1` and a new source are appended; if it merely decayed, nothing is.

**Why this way.** It always returns to `L0`, whatever the rule used to be. A level is a category of evidence, not a shelf by weight: levels are earned by consolidation, and a line placed straight at the top would displace no one and would zero the timer by which that level waits for material from below. A decayed line returns exactly as it was: it lived out its horizon without refutation, there is nowhere to take a new source from, and its weight will lift it quickly. A refuted one arrives with an `inverse`, which weighs double, and the same queue decides its fate. The cycle closes: observation → rule → violation → observation.

A rule from `~/.claude` returns to the `L0` of the project in whose session it left: there are no other shelves in memory. The price is named: the line brings sources from projects that shelf has never seen, and its clock changes — it was counted on the whole session index and will go on by one project's sessions. And if the session belongs to no project — started in the home folder or in MORF itself, with no shelves at all — the exit waits: `--seal` will not record a `returned:` where no return address exists, or the log would claim a move that never happened.

**Why not otherwise.** Returning as a new line would zero the counters and the whole source list — the very thing the register exists for. A rule that failed once would come back to memory as a nameless candidate, and in half a year would rise again looking fresh.

There is no second exit — deletion — for the same reason. That is what `moves` in the line is for, see [[foundation]], and the log on disk. Rules are not eternal; only sources are.
