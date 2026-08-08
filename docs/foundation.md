---
type: doc
description: the shared foundation — archive, time scale, /morf:why, settings, audit
tags: [morf, infrastructure]
---

# Foundation

**EN** — [RU](ru/основание.md)

**What this is.** The machinery under the three layers: the conversation archive, the time scale, traceability, settings, the audit.

**What for.** None of the layers works on its own. An observation without a source is invalid, a source without an archive is a dead link, a score without a time scale cannot be computed. This is a shared foundation, not a fourth category of information.

---

## The conversation archive

**How it works.** Two hooks, no agent involvement, described in the [hooks reference](https://code.claude.com/docs/en/hooks): [`SessionStart`](https://code.claude.com/docs/en/hooks#sessionstart) and [`SessionEnd`](https://code.claude.com/docs/en/hooks#sessionend).

`SessionStart` adds a row to `.morf/sessions.md` and registers the session. Registration happens at the start rather than the end: otherwise `/morf:handoff` would have nothing to reference — the row would not exist yet.

A copy into the archive is made on every `/morf:handoff`: the session transcript, and the subagent files kept in the folder Claude Code names after the session.

The files lying *beside* that folder are other sessions' transcripts, not this one's children. Collecting by modification time instead — which is what an earlier version did, meaning to catch the subagents — gathered peers, stored every session twice and never copied a subagent at all.

Copied whole, with all structure: turns, agents' reasoning, tool calls.

**Why this way.** A copy rather than a reference to Claude Code's own store: that store is wiped on a schedule, and without the raw data the identifiers become dead links, taking the whole of traceability with them. The archive's job is that the place a reference points to does not disappear in three years or five.

Copying on `/morf:handoff` rather than only at the end is about marking, not reliability. **The copy ends exactly where the piece of work ended**, so the number of the last line is the mark, and the range between two calls defines the stretch without a single guess. A reference takes the shape `s:260803-a41f#412-980`, and `/morf:why` opens not a six-hour conversation but the stretch a line came from.

After that Claude Code's own store is needed only for sweeping in sessions that were cut short, so `cleanupPeriodDays` in the [settings](https://code.claude.com/docs/en/settings) needs no more than a month.

**The archive does not expire.** A reference appears together with the index row, that is, with the system already running, and a copy is never deleted — "older than the retention period" cannot happen here.

A missing file means the session was cut short before the copy. `SessionStart` writes the state — into `.state/<working folder>.json` — and `/morf:handoff` copies the files, so there is a window: kill the session hard and the identifier exists while the folder does not. The loss is apparent rather than real. **Claude Code writes the transcript as the session goes, not at its end**, so the conversation itself is intact in `~/.claude/projects/`, and the next `SessionStart` sweeps it in.

The file is named after the folder because that is the only key `/morf:handoff` is given — a command is told no session id. What it holds, though, is **an index: every session that registered in that folder, each with its own transcript and its own mark**. A single record per folder made the folder an identity, and it is not one. Whichever session started last owned the slot: `/morf:handoff` answered another session's reference, a session still running in a second window was reported as cut short, and a resume wrote the mark of a stretch already handed off back to zero — the whole conversation came back as an unread debt from line 1, its observations already in the memory. A session is identified by the four characters of its id, so a resume past midnight is still the same session and not a second one.

A copy is not enough, though: a session that ends without `/morf:handoff` leaves a stretch nothing was made of. That cannot be finished mechanically. So `SessionStart` works out how far each ended session of this folder got and **tells the agent the unprocessed stretches**: its stdout reaches the session context. The working order says to start with `/morf:handoff` on that reference.

Ended, not merely other. `SessionEnd` says so outright, but the case worth sweeping — window closed, process killed, machine shut down — is exactly the one that hook never sees, so a transcript left untouched for two hours counts as over too: Claude Code appends to it on every turn, and silence that long is not a session thinking.

**The memory is the evidence, the marker is only bookkeeping.** A stretch written up names itself as its source, so a debt is dropped for whatever the memory already cites. There is one memory to read — the levels in `Observations/` and `dropped.md` — and a worktree's own observations land in it too, because a worktree shares the main checkout's `.morf` rather than keeping one named after the task. Bookkeeping is what went wrong here twice; what a line says about where it came from cannot be wrong in the same way.

**Nothing but copying writes into the archive.** It is filled by exactly one path — from Claude Code's history, by a hook rather than a tool. So any tool call touching `Transcripts` is either a mistake or an attempt to erase evidence, and telling them apart is pointless: there are no legitimate cases.

Writing and deleting there are therefore blocked by [`PreToolUse`](https://code.claude.com/docs/en/hooks#pretooluse): `guard-archive.py` exits with code 2, the call never runs, and the reason goes to the agent. It does not affect you — you edit files outside the agent's tools.

This is the only place where enforcement is introduced immediately rather than through accumulated `E`. The grounds are the usual ones: the condition is mechanically unambiguous, and closing off the view here costs nothing, because no legitimate cases remain behind the hook.

**Why not otherwise.** Storing transcripts as notes would put them on the map, and the agent would start spending context on reading old context.

Setting `cleanupPeriodDays: 0` is not an option: the documentation calls it "never clean up", but a known bug turns off transcript writing altogether.

---

## What the memory owes

**How it works.** Collecting was the only stage that ran by itself. Consolidation, the audit and the facts map each waited for someone to read the working order and recall the cadence, and for the whole life of this memory not one of them ever ran. Nothing about that looked wrong: an empty upper level is a correct state, an audit that has never run reports `last: none`, and a map with no articles is a map with no articles.

`due.py` derives every obligation from what is already on disk, so nothing new is bookkept. A level is owed material when the level below carries a session it has never seen and enough of the project's sessions have passed since. The audit counts sessions against the id in `audit.md`. The map is stale when an article is newer than it. `SessionStart` prints them all.

**Considered and declined is an outcome, and it is written down.** Weight is often too low to promote anything, and that verdict has to close the debt or the debt is noise. It closes it the same way every debt here closes — by appearing in the memory: the upper level names the sessions it weighed on a `<!-- considered: s:… -->` line, and they stop being unseen, because sources are read from the whole file and not only from its lines. Bare ids there, never a `#range`: a range reads as a stretch somebody wrote up, and would clear a handoff debt nobody paid.

A level *holds* what its lines cite and has *seen* that plus what it declined, and only the second reading counts the verdict. Read the other way round, a decline travels upward as material the level above has never received — while no line up there carries it, so there is nothing to weigh and no way to answer.

The alternative was tried: infer the decision from the file being newer than the one below. It was worse than nothing. `score-memory.py` rewrote every scored level on each run, so the step the working order puts **first** discharged every consolidation debt in the store before anyone had looked at a single line — and the store then reported itself as owing nothing. A timestamp is a proxy for having decided; the decision is the record, and only the record can stand in for it.

**Why this way.** A debt is the agent's, so it is put in front of the agent — on [`UserPromptSubmit`](https://code.claude.com/docs/en/hooks#userpromptsubmit), whose stdout reaches the context, on **every** turn until the debt is gone. The pressure is not in blocking once but in arriving every time: a notice said once at session start is exactly what this replaces.

Once is not enough, though: a turn told at its start still ends however it likes. [`Stop`](https://code.claude.com/docs/en/hooks#stop) is the one point where the answer is written and the debt is still there, so it sends the turn back — the work gets done, or the answer says it was left. `stop_hook_active` marks a turn already returned once, because blocking twice is not pressure but a hang.

**Why not otherwise.** An earlier version exited 2 on the prompt instead, which discards it. That made a person retype what they had just written to pay for what an agent had forgotten, and the owner's part in this system is to approve a hook, nothing else. Enforcement that bills the human is worse than none: it teaches them to remove the hook.

---

## The index and the time scale

**How it works.**

```
| id | date | project | about |
|---|---|---|---|
| s:260803-a41f | 2026-08-03 | shader-lab | shader cache |
```

The row is added by the hook; the "about" column is filled by `/morf:handoff`.

An identifier `s:260803-a41f` is the date as YYMMDD plus the first four characters of the session uuid.

**Why this way.** Two functions in one structure. The obvious one: turning an identifier into a path. The more important one: the order of the rows sets the age of events. One `.morf` is one project, so every row is this repo's and the whole index is the time scale — there is no column to filter on. Age is measured in sessions, and the data for it is already here — no separate journal needed.

The `project` column survives as a label, not a divider: it names the repository the `.morf` lives in, the same on every row, read back only in `/morf:why`.

The date in the identifier is human-readable, the uuid distinguishes several sessions on the same day. It is the only calendar value in the whole model, and it takes no part in the arithmetic.

**Why not otherwise.** A separate time journal would have to be linked to the records, and there is nothing to link by: an observation has no identifier of its own, only sources.

---

## Traceability

**How it works.**

```bash
python3 .morf/scripts/read-session.py 260803-a41f#412-980 cache
```

`/morf:why` walks the chain: line → its `s:` → the index → the archive → a readable stretch of conversation. Agents' reasoning is shown.

**Why this way.** It works the same for all three layers because the identifiers are shared. This is the answer to "not losing the index when compacting": compacting loses text but not links — on every consolidation the sources of merged lines are added together. A rule grown from observations carries a list of sessions spanning years, and any of them can be opened.

Reasoning is not skipped because the answer to "why did we decide that" usually lives there rather than in the turns.

**Why not otherwise.** `/morf:why` is not part of the route: it is a lookup, not a transition. It moves and changes nothing, which is why no arrows lead out of it on the canvas.

---

## Move history

**How it works.** A comment attached to the record:

```markdown
<!-- moves: s:260901-aa11 fact, s:261102-bb22 observation -->
```

Four possible states, the exits of the verdict: `observation`, `fact`, `rule`, `dropped`.

**Why this way.** Sources let you trace where the content came from. They do not let you trace what the system did with it — and that is needed to see oscillation between fact and observation, and to know that a rule already failed once and came back.

The comment is markup: a notes editor renders it away, so the bookkeeping stays out of sight while you read the record. It is not free for the agent, which reads the file raw — which is why it is one line and holds the moves and nothing else.

**Why not otherwise.** A separate move journal would have to be linked to the records, and there is nothing to link by. Keeping it on the record itself solves that without a single new structure.

---

## Settings

**How it works.** `.morf/scripts/config.json` holds numbers for the script, next to the script. The canvas shows that same file as a link node, so no copy of the values exists anywhere.

`levels.md` is generated from it: the levels with their horizons and limits, in a form the agent reads. Two files, but not two stores of one thing — a source and its derivative. Delete `levels.md` and it comes back; `config.json` cannot be restored from anywhere.

**Why this way.** The division worth remembering: **`config.json` is for the code, `CLAUDE.md` and the skill are for the agent.** Whatever the agent must know lives where it loads by itself; whatever only the code needs lives next to the code. For a new setting there is one question: who reads it.

They also differ in force. A number in the config **compels**: the script substitutes it into the formula, and disagreeing is impossible. An instruction only **inclines**: the model usually follows it, but may deviate, and there is no check.

**Why not otherwise.** One version kept the weights in a canvas node and had the script parse `.canvas`. A diagram is not configuration: a broken diagram would break the arithmetic.

Another version kept the language in `config.json`. Language is an instruction to the agent, and `config.json` never reaches the context: the agent would have to open a file for something that should be in front of it, or the setting would be duplicated. Putting instructions next to numbers also creates the false impression that instructions are enforced too.

**Language.** Imperatives in English: instructions, commands, rules, agent definitions. Everything indicative — observations, fact articles, replies to you — in the language you work in.

---

## The audit

**How it works.** `/morf:audit` runs on every tenth session of the project. `audit.md` holds the identifier of the last audit, and the check is a count of index rows after it.

It compares what was displaced over the last hundred sessions of the project with what has been written since the previous audit. It moves nothing.

**Why this way.** Diagnostics, not machinery: it counts **for you**, not for the machine, which is why it lives apart from consolidation.

Two readings of the result, and they call for different fixes: matched in the same words means the displacement threshold is too low; matched in different words means the wording is unstable and one observation is being recorded twice under two names.

**A report may be empty, and that is a good result.** Inventing findings to look useful is the one way to ruin an audit.

**Why not otherwise.** There is deliberately no calendar schedule: a month of idleness and a month of daily work give incomparable material, while ten sessions are comparable by definition. It is the same reason the calendar was taken out of decay.

A built-in similarity check on word overlap was considered and rejected: it would need stop lists, significance thresholds and morphology — heuristics on top of heuristics. Once every ten sessions, over fifty lines, comparison can be done by meaning, and all of that falls away.

---

## Outside the system

**Tasks.** The state of work: what we are doing, in what order, who took it. Not verified by experience, gathering no evidence, living until closed rather than until refuted. No mechanism of memory applies — tasks live wherever the process is run.

The link is one-way: a planner reads memory and gets better for it, and writes nothing back. A closed task produces no observations by itself — they are produced by something unexpected inside the work, and recorded by `/morf:handoff`.

The one reverse signal: a task that came back into work means somebody's prediction did not hold.

**Hence why `use` stays a self-report.** Applying a record happens in the work, and the work is not our layer. There is nothing to observe it with from outside, and no refinement of the model will change that. The sign that the agent is inflating it: the list by `R` stops differing from the full list.
