---
type: doc
description: setup steps, command texts and the CLAUDE.md template
tags: [morf, setup]
---

# Setup

The model lives on the canvas at `MORF/Memory/model.canvas`; the reasoning is
in these notes. This file holds only what is in neither: how to install and the
texts of the commands.

## The quick path

Double-click `Install-MORF.command`. It asks three things — which folder the `MORF`
folder goes into, what the first project is called, and which language to keep
observations and fact articles in, picked from a list that opens on the one your
system already uses — then drops the plugin into
`~/.claude/skills/morf` and lays the files out in `MORF`. No terminal, no
permission prompts.

It resolves earlier installs on its own: a marketplace copy, a half-installed
folder, a pointer to another MORF. Memory records are never touched — only
what is missing gets created.

On first launch macOS warns about an unsigned file: right-click → Open → Open.

Through the marketplace, if you prefer:

```
/plugin marketplace add e0068/MORF
/plugin install morf@morf
```

## What ends up where

```
MORF/
├── Memory/
│   ├── Scripts/        five scripts and config.json
│   ├── Transcripts/    the conversation archive
│   ├── <project>/      L0 … L3, dropped
│   ├── sessions.md · audit.md · levels.md
│   ├── TAGS.md · INDEX.md
│   └── model.canvas
├── Facts/              fact articles
└── Docs/               these notes
```

`~/.claude/morf-path` holds the path to the folder; every script reads it, so
nothing else needs configuring. Nothing above that folder is ours, and no
script looks there.

## The commands

The plugin ships them; the texts below are for reference and editing.

### `/morf:handoff`

```markdown
Reconcile what happened with what the system predicted.

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/archive-session.py --handoff`.
   It copies the transcript into the archive and prints a reference to the
   stretch written since the previous call: `s:260803-a41f#412-980`.
   Use that reference as the source for every line you write below.
   If the session start reported an unfinished stretch, use its reference
   instead — the copy for it is already archived.

2. Expected outcomes are counters on existing lines; add no new lines for them:
   `hit` the prediction held · `use` the line changed what you did ·
   `miss` the prediction did not hold · `inverse` the opposite happened.

   `inverse` also creates a new line: the opposite is itself unexpected.
   A refutation matters more than a new finding — never skip it for brevity.
   If a rule received an `inverse`, tell me at once: it is suspended now.

3. Unexpected outcomes become a new line in `MORF/Memory/<project>/L0.md`:
   `- hit:1 use:0 <what happened> (s:<ref>)`
   Write it in the indicative. An observation is what occurred.

4. If a conclusion about how to act formed during the work, do not discard it.
   Record the observation in the indicative, mark it `↑`, and attach the
   proposed rule wording below it.

5. Invent nothing. If it did not happen in this session, it is not written.

Show me what you intend to write before writing it.
```

### `/morf:why`

```markdown
Take me back to the conversation a line came from.

The argument is a fragment of an observation, an article or a rule.

1. Find it across `MORF/Memory/`, including `dropped.md`, in fact articles
   and in rule files. Say where it lives.
2. For each source, run:
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/read-session.py <ref> <keyword>`
   A reference may carry a line range: `260803-a41f#412-980`.
3. Show the fragments in chronological order, with date and project from
   `sessions.md`. Do not skip the agents' reasoning — the answer is usually there.

The archive never expires. A missing file means the session was cut short
before its stretch was copied; the next session start sweeps such transcripts in.

Finally, ask what to do with the line: keep it, restate it, or drop it.
```

### `/morf:audit`

```markdown
Audit the memory of the current project. Change nothing: report only.

1. Read `MORF/Memory/<project>/dropped.md` — entries displaced within the
   last hundred sessions — and every line added since the `last` session id
   recorded in `MORF/Memory/audit.md`.

2. Compare them by meaning, not by wording. Report pairs where something
   displaced earlier was written down again as a new observation.

   Same thing, same words -> the displacement threshold is too low.
   Same thing, different words -> the wording is unstable, and one
   observation is being recorded twice under two names.

3. Count and report, without interpreting: lines added, promoted, displaced;
   lines that became rules and lines that became facts; lines sitting at the
   top level for over three periods without an exit; whether `dropped.md`
   grows faster than the levels.

4. Append the result to `MORF/Memory/audit.md` with the current session id
   as the new `last`. Keep previous entries — this file is a history.

Say plainly if there is nothing to report. A quiet audit is a good result.
```

## The `CLAUDE.md` next to MORF

The installer creates this file if it is missing and keeps the `Language`
section between markers, so a repeat install replaces only that section. The
rest is yours; the working order itself lives in the plugin's `morf` skill.

```markdown
# Notes

Memory lives in `MORF/Memory`, fact articles in `MORF/Facts`.
The working order is in the `morf` skill.

## Never

- Do not touch `[S= R= t=]` by hand: `score-memory.py` writes them.
- Do not edit `TAGS.md`, `INDEX.md`, `sessions.md`, `levels.md`: generated.
- Never write to or delete from `MORF/Memory/Transcripts`.
- Delete nothing else either. Displaced lines go to `dropped.md` with sources.

<!-- morf:language -->
## Language

Imperatives in English: instructions, commands, rules, agent definitions.
Everything in the indicative — observations, fact articles and replies to me
— in Russian.
<!-- /morf:language -->
```
