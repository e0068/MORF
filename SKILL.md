---
name: morf
description: MORF — Memory of Observations, Rules and Facts. Working order for the three-phase memory: what to read at session start, how to consolidate the levels, and how an observation turns into a rule or a fact article. Use whenever a session begins where a MORF folder is set up, when the user asks about memory, observations, facts or rules, or when a session-start hook reports an unfinished stretch.
---

# MORF

**M**emory **o**f **O**bservations, **R**ules and **F**acts, kept as plain
markdown files. Observations accumulate and are consolidated level by level:
what matures into "do it this way" becomes a rule, what stays true but yields
no action settles as a fact article.
The full model is on the canvas at `MORF/Memory/model.canvas`;
the reasoning is in `MORF/Docs/`.

## At session start

1. If the session start reported an unfinished stretch from a previous
   session, run `/handoff` for that stretch first, using the reference
   it gave you. The transcript is archived, but nobody turned it into
   observations yet. This one is enforced rather than advised: until the
   stretch is handed off, `gate-handoff.py` refuses every prompt that is not
   about the handoff itself, and hands the refused text back to be resent.

2. Read for the current project: `MORF/Memory/<project>/L3.md`, `L2.md`,
   `L1.md`. Do not read `L0.md` — it is input for consolidation, not memory.

3. Read `MORF/Memory/levels.md`: it lists the levels, their horizons and
   line limits. It is generated from `Scripts/config.json`; never edit it.

4. If the first level changed or is approaching its limit, consolidate
   before starting work. The session start says how full the inbox is and
   refuses work once it is at the limit, where new lines displace old ones:
   - recompute scores: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score-memory.py`
   - work top down: fill `L2` from `L1` first, then `L1` from `L0`.
     Bottom up a line would climb two levels in one pass.
   - group related lines into clusters, then try to state an imperative:

     stated, enough weight, already tried against what happened -> rule
     stated, weight too low                                     -> leave it
     cannot be stated                                           -> a fact article
     weight decayed                                             -> `dropped.md`

   - promote a line one level up, displacing the weakest by `S`
   - report what changed in a single table

5. What the memory owes arrives on **every** turn, not once at the start: an
   unread stretch, a consolidation the levels wait for, an audit past its ten
   sessions, a facts map older than its articles. All of it is yours to
   discharge and none of it is mine to be asked about — I am not the timer,
   and I am not the one who forgot. Never turn a debt of yours into a
   question for me. `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/due.py --all`
   says it for every project at once.

## Writing

- Memory line: `- hit:N use:N miss:N inverse:N text (s:ref)`. Omit zeros.
  A line without sources is invalid.
- An imperative produced by prefixing "do not" to an observation is a
  restatement, not a rule. A real rule adds what the observation lacks:
  what to do instead, under which condition.
- Fact articles live in `MORF/Facts` and nowhere else: the map is built from
  that folder alone, so an article written elsewhere is invisible.
  They are articles about a phenomenon, not one fact per file.
  Before writing, look for an existing article via `TAGS.md` and `INDEX.md`
  and append a section with its sources. Link related phenomena with `[[...]]`.
  When the phenomenon is already covered, add your source to that paragraph
  instead of writing a second one saying the same thing.
- A tag earns its place when at least two articles carry it. Never invent
  tags outside `TAGS.md`; propose additions instead.
- A folder name states its relation to its parent. Read a path bottom-up as
  a phrase before creating it: `MORF/Memory/Memory` would read as "memory
  of memory", which is not a thing.

## Never

- Do not touch `[S= R= t=]` by hand: `score-memory.py` writes them.
- Do not edit `TAGS.md`, `INDEX.md`, `sessions.md`, `levels.md`: generated.
- Never write to or delete from `MORF/Memory/Transcripts`. It is filled by
  copying from Claude Code's own history and by nothing else. A hook blocks it.
- Delete nothing else either. Displaced lines go to `dropped.md` with sources.
- If a rule is violated often, propose making it a hook, but never move it
  yourself. A hook is a hard constraint imposed from outside: it closes off
  not only the violation but the view beyond it.

## Language

Imperatives in English: these instructions, commands, rules, agent definitions.
Everything in the indicative — observations, fact articles, and your replies
to me — in the language set in the `CLAUDE.md` next to MORF.
