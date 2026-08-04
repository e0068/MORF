---
type: doc
description: the rule layer — two axes, for and against, track record, hardness; how it works and why
tags: [morf, rules]
---

# Rules

**EN** — [RU](ru/правила.md)

**What this is.** Instructions on how to act. Imperative mood, applied anywhere, never verified by observation — only obeyed or broken.

**What for.** A rule is the only full exit from memory: the whole queue exists for it. A fact covers the case of "true, but no action follows", `dropped` covers "did not hold up".

---

## Not a duplicate of the observation

**How it works.** A mood check at write time: if the line wants to be written as "do" or "do not", it is a rule and does not go into memory.

**Why this way.** "X breaks the build under Y" and "do not use X" are different statements. The first is refuted by observation, the second is cancelled by decision. The first lives in memory with its sources, the second in rules with a reference to them.

A side benefit of the test: an indicative wording forces you to name what was actually observed. "Do not use X" hides the grounds, "X breaks the build under Y" presents them — and is therefore usable by `/morf:why`.

**Why not otherwise.** It looks like duplication and one of the two could be dropped. It cannot: they have different life cycles. An observation decays and is refuted; a rule goes stale and is cancelled; the two events are independent.

---

## Two independent axes

Merging them was the first version's mistake: `~/.claude/CLAUDE.md` stood "above" the project file, though it is merely wider. A project rule can be a hard hook; a general one can stay advice.

### Reach and frequency: where to put it

| Address | When it loads |
|---|---|
| `~/.claude/CLAUDE.md` | always, in every project |
| `CLAUDE.md` of the project | always in this project |
| `.claude/rules/` with `paths:` | when working with files matching the pattern |
| `SKILL.md` | by the meaning of the task |
| an agent definition | when that role is invoked |

**These are addresses, not levels.** There is no summit, and movement goes both ways: wider on confirmation in a second project, narrower on refutation.

**The contour is a file.** Changing the contour means moving the line. In another project a rule from the project `CLAUDE.md` is not "hidden" — it does not exist. This is where rules differ from facts, whose contour is merely a field.

**The last two rows are the key ones and the most often missed.** `CLAUDE.md` loads always, so only the frequent belongs there. A rare rule is displaced from it not into the bin but into a skill or an agent definition. That explains where skills come from rather than postulating them: **a skill is a set of rarely needed rules, loaded by the meaning of the task.**

### Hardness: context or enforcement

A rule in `CLAUDE.md` is context, not an obligation. If it has to fire at a particular moment, it is a hook or `permissions.deny`.

A high `E` promotes it. But you make that move, and it is the single manual point in the whole system.

**A hook is a hard constraint imposed from outside: it closes off not only the violation but the view beyond it.** After it you only see what it lets through, and a bad hook is indistinguishable from a perfectly working rule. So a high `E` reads not as "time to forbid" but as "time to decide whether we are ready to stop looking".

The limit: only the mechanically unambiguous qualifies. A hook on a debatable condition gets in the way of work, and it will be switched off wholesale along with its useful part.

---

## Two bundles of sources

**How it works.** *For* — the observations that produced the rule. *Against* — those that lost at the time. **The losers are not discarded** and keep gathering confirmations.

This repairs a defect present from the start: a rule was created from the winners, the rest hung around unlinked and sooner or later decayed. The system was systematically losing exactly the half of the picture needed for a review.

**Both bundles are alive.** Break the rule and regret it — *for* grows. Break it without consequence — *against* grows. Comparing the weights literally means "how many times we regretted breaking it" against "how many times we regretted obeying".

**No need to freeze the weight of *for*.** After a rule is adopted, confirming observations stop arising on their own: the agent acts by the rule rather than re-testing its grounds. They grow only from violations that went badly — that is, from genuine tests of strength.

---

## Review

A weight of *against* that outgrows *for* sends the rule to review. The argument is not blocked; it simply has an entry price.

This cancels the separate entity of a "decision" that was proposed at one point. The argument for it was that a rejected branch was never lived through, has no evidence, and therefore always loses. But it does have **arguments**, and they are alive: the observation "our own library would give control over the grid" is confirmed every time the grid gets in the way. The losing side gathers weight not from lived experience but from repeated collisions with a limitation.

**An argument landing in both bundles is diagnostics.** Either a judgement is baked into the observation instead of a fact — then rewrite it down to the fact, the judgement lives in the rule — or the rule is too broad and needs splitting. It cannot be decided automatically: both outcomes are legitimate.

One observation may well stand for one rule and against another; that is normal. The problem exists only inside a single rule.

---

## Track record

**How it works.** The bookkeeping sits next to the rule inside a block HTML comment: such comments are stripped before the context, so they are visible to you and the script but cost no tokens.

```markdown
- do not use X in release builds
<!-- A14 V3 X̄6 for:(s:…) against:(s:…) -->
```

- `A` — opportunities to apply, in a **sliding window**. A cumulative counter would equate a rule that has been internalised with one that was never needed: both show no recent violations.
- `V` — violations.
- `X̄` — the **median** gap, in sessions of the same project, between a violation and its discovery. One case with a huge gap would otherwise skew everything.

```
E = (V / A) × X̄
```

Expected exposure: how much work on average runs on false grounds because of this rule.

**`X̄` measures risk, not damage.** It counts not what happened but how many chances there were for it to happen. A case where you got lucky must not lower the figure: luck is not a property of the rule. A separate damage counter is not worth adding — it is almost always zero, it creates the impression that the absence of losses says something, and it demands a self-report from the agent.

**Justifying a rule in prose is unnecessary.** A rule has a track record and the sources of both bundles, and `/morf:why` reaches the raw conversations from them. A retelling would be a fourth copy of the same thing — unverifiable and going stale silently, because it has neither counters nor sources.

**Decay is counted in applicabilities, not days.** A release rule applies once a month, a code-style rule hourly; extinguishing them at the same pace makes no sense.

---

## Narrowing and death

**A refutation narrows rather than cancels.** `do not X` meets a refutation in another project and becomes `do not X when Y`. Compacting rules is the opposite of compacting observations: there lines merge, here they split.

Hence a natural drift: the more often a rule was narrowed, the narrower it is, the lower its `A`, and the more surely it slides along the reach axis into a skill. That is a normal life cycle, not degradation.

**`A ≈ 0`** — the situation never arises, the rule is dead. Remove it regardless of anything else.

**A rule refuted outright returns to observations** as a line with `inverse` and a new source, not to an archive. The cycle closes: observation → rule → violation → observation.

**Why not otherwise.** Deleting a rule would lose the history: the next identical one appears in six months looking fresh, though it already failed once. That is what `moves` in the line is for — see [[foundation]].

---

## Rules you cannot judge

**How it works.** Rules divide into established and derived.

Established — design, process, who reviews what: you write them and owe no justification.

Derived — code and anything requiring expertise you do not have:

1. import the published conventions of the language and the linter defaults, marking the block as inherited and unverified;
2. promote by seniority — it lived without refutation, so move it, keeping the sources;
3. only on a recorded case of an error the rule would have prevented.

**Why this way.** The third point guards against a closed loop: the agent proposes a rule from general considerations, then confirms it itself, and in half a year `CLAUDE.md` consists of well-sounding platitudes nobody checked. You cannot check the content, so the mechanism must.

A rule can be judged by consequences even without expertise in the subject. "Entities are covered by protocols" cannot be assessed; "after this rule there was less rework" can. The mechanical check: run the candidate against recent diffs with a reviewer agent and see whether it would have caught anything real.

**Why not otherwise.** Inventing rules yourself in an unfamiliar area is the worst option: they look sensible and are checked by nothing. Importing a ready set at least rests on someone else's experience.

Speeding up the intake by letting the agent promote rules on general considerations is a temptation to resist. For the first months there will be few rules, because errors have to be made and noticed first. That is the price of an honest mechanism; if too little arrives for code, importing another ready set of conventions is the more honest fix.

**Demotion.** A rule that stopped firing or started getting in the way goes back to `L3.md` with a new source. Rules are not eternal; only sources are.
