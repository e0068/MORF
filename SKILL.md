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
   observations yet. This is a debt, not an advisory: `due.py` puts it in
   front of you on every turn until the stretch is handed off, and will not
   let a turn end while it stands. The debt lifts by itself once the stretch
   is written up — its reference then appears as a source in the memory.

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

     stated, S >= rulesInScore, use/hit >= rulesIn -> rule
     stated, either threshold not met              -> leave it
     cannot be stated                              -> a fact article
     weight decayed                                -> `dropped.md`

     The thresholds are in `Scripts/config.json`. A rule also needs at least
     one `hit`: `hit` is the denominator, so a line that changed decisions but
     was never confirmed waits.

   - a level fills with the cluster's imperative, not with a line that
     happened to be held twice — its `hit` is the cluster's weight and its
     sources are all of theirs. Look at what the level already holds before
     deciding nothing qualifies for it.
   - promote a line one level up, displacing the weakest by `S`
   - append your verdict to the level above, on its own line, naming every
     session you weighed — promoted or not:

     `<!-- considered: s:260801-aaaa s:260801-bbbb -->`

     Session ids only, never a `#range`: a range there reads as a stretch
     someone wrote up, and would clear a handoff debt nobody paid. Append a
     new line each pass and never edit an earlier one — they add up, and
     rewriting one reopens what it had closed. That is what closes the debt,
     the same way a handed-off stretch closes its own: by appearing in the
     memory. An unwritten decision is indistinguishable from work never done.
   - report what changed in a single table: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/trace.py --show`
     renders it from disk — a shelf per row, a level per column, each cell
     `count (+in −out)`. Show that matrix rather than an account of your own;
     it is the one report you cannot overstate. The same table prints itself on
     `Stop` whenever a turn moved memory, so after a `/handoff` too.

5. What the memory owes arrives on **every** turn, not once at the start: an
   unread stretch, a consolidation the levels wait for, an audit past its ten
   sessions, a facts map older than its articles. All of it is yours to
   discharge and none of it is mine to be asked about — I am not the timer,
   and I am not the one who forgot. Never turn a debt of yours into a
   question for me. A turn does not end while a debt stands: either do the
   work or say in the answer that you left it, and why. `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/due.py --all`
   says it for every project at once.

## Writing

- Memory line: `- hit:N use:N miss:N inverse:N text (s:ref)`. Omit zeros.
  A line without sources is invalid.
- An imperative produced by prefixing "do not" to an observation is a
  restatement, not a rule. A real rule adds what the observation lacks:
  what to do instead, under which condition.
- A rule's text goes to one of the five addresses in `MORF/Docs/rules.md`;
  its accounting goes to `MORF/Rules/map.md`, a line per rule in the shape of
  a memory line. Nothing of ours is written into the file outside the contour.
- Putting a rule into a file is three steps, and the last two are yours to run,
  never the owner's: write the text, then
  `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/rules.py --track <file>` if that file
  is not watched yet, then `rules.py --adopt <file> "<the rule text>"`, which
  writes both the register line and the `added:` entry. A rule whose file was
  never tracked is invisible to the layer: it will not be missed when someone
  deletes it.
- The layer accounts for what MORF wrote and for nothing else. Instructions the
  owner put in these files are theirs: they work as they always did, and they
  are not yours to notice, count, propose or ask about. Never offer to take one
  in. `--adopt` exists for the owner to name a line themselves, and only then.
- When a watched file drifts, discharge it in this order: read
  `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/rules.py --diff`, write what changed
  into that file's `*.log.md`, then `rules.py --seal <path>`.
- A `·` line in `--diff` counts what moved in that file without touching a
  rule, and it is cumulative since the last seal. Discharge it the same way:
  an `outside: N line(s) changed, no rule touched` entry in the log, then
  `--seal`. Left alone it only grows, and the next real count is measured
  against a stale copy.
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

- Do not touch `[S= R= t=]` by hand: `score-memory.py` writes them, in
  `MORF/Rules/map.md` as well as in the level files.
- Do not edit `TAGS.md`, `INDEX.md`, `sessions.md`, `levels.md`, `TRACE.md`: generated.
- In `MORF/Rules` the logs and the counters in `map.md` are written by hand;
  `*.snap.md` is a snapshot the scripts keep, and `[S= R= t=]` in `map.md` is
  written by `score-memory.py`. No log is ever deleted.
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
