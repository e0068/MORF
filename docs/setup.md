---
type: doc
description: setup steps, command texts and the CLAUDE.md template
tags: [morf, setup]
---

# Setup

**EN** — [RU](ru/установка.md)

The model lives on the canvas at `.morf/model.canvas`; the reasoning is
in these notes. This file holds only what is in neither: how to install and the
texts of the commands.

## The quick path

MORF is dropped into a repository, not installed centrally. Run the installer
inside the repo you want it in:

```
tools/install.sh                 into the git top-level of the current directory
tools/install.sh <target-repo>   into that repository
```

It lays down `<repo>/.morf/` — the scripts, hooks, commands and docs, plus an
empty memory skeleton where one is missing — wires the six hooks into the
repo's own `.claude/settings.json` (merging, never clobbering existing
settings), and writes the content-language block into the repo's `CLAUDE.md`.
Memory records are never touched; a code file it replaces on a re-install is
kept beside it with a timestamped `.bak`. Re-running is idempotent.

By default it adds the memory *data* to the repo's `.gitignore` while keeping
`.morf/scripts`, `hooks` and `docs` committable — a worktree needs
the scripts present for its hooks to fire. Pass `--private` to skip that step
and let the whole `.morf`, data and all, travel with the repo. The content
language defaults to the system locale; `--lang <Name>` sets it non-interactively.

No clone required: `tools/build-release.py` builds a self-extracting
`dist/install-morf.sh` that carries the payload and runs the same installer —
`sh install-morf.sh <target-repo>`, arguments passed straight through.

## What ends up where

```
<repo>/
└── .morf/                  code and data together, one folder inside the repo
    ├── scripts/            the scripts and config.json
    ├── Observations/       L0 … L3
    ├── dropped.md          displaced lines
    ├── Transcripts/        the conversation archive
    ├── Facts/              fact articles
    ├── Rules/              snapshots, logs and the rule register
    ├── sessions.md · audit.md · levels.md
    ├── TAGS.md · INDEX.md · TRACE.md
    ├── model.canvas
    └── docs/               these notes
```

There is no pointer and nothing to configure. The home is the `.morf` the
running script lives in — its own parent's parent — so the path is not stored
anywhere, it is where the code sits. One repository is one `.morf` is one
project is one memory: the `<project>` shard is gone, the levels live in
`Observations/`, and nothing above `.morf` is ours.

A git worktree checks out `.morf/scripts` but not the data; it shares the main
checkout's `.morf`, found through the common git dir, so every worktree feeds
the one memory rather than a folder named after the task. Only for loose,
non-git use does the old order survive as a last resort: `MORF_HOME`, then the
`~/.claude/morf-path` pointer, then `~/MORF`.

**Whether `.morf` is committed is the repository's call, not MORF's.** A public
repo adds `.morf/` to `.gitignore` and keeps the memory local; a private one
commits it, so the memory travels with the code. Either way it is code and data
in one place, dropped in and self-contained.

## The commands

The plugin ships them; the texts below are for reference and editing.

### `/morf:handoff`

```markdown
Reconcile what happened with what the system predicted.

1. Run `python3 "$CLAUDE_PROJECT_DIR/.morf/scripts/archive-session.py" --handoff`.
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
   If a rule received a `miss` or an `inverse`, it leaves the rule layer in
   this same session: its counters go up in `.morf/Rules/map.md`, the move is
   written into that file's `*.log.md` as `returned:`, and the line goes back
   to `L0` with its counters, sources and move history. Tell me at once.

3. Unexpected outcomes become a new line in `.morf/Observations/L0.md`:
   `- hit:1 use:0 <what happened> (s:<ref>)`
   Write it in the indicative, in the language set in CLAUDE.md.
   An observation is what occurred.

4. If a conclusion about how to act formed during the work, do not discard it.
   Record the observation in the indicative, mark it `↑`, and attach the
   proposed rule wording below it, in English.

5. A fact article that took part in a decision gets `applied` raised in its
   front matter — the same event `use` records for an observation. If it is
   being applied again, return the line it came from to `L0.md` whole: same
   wording, same counters, same sources. A new line would be a forgery, and
   `/morf:why` has to lead back to the same conversations.

6. Fill the `about` column of this session's row in `.morf/sessions.md`:
   two or three words on what the work was about. The hook writes the row
   before the work starts and cannot know that.

7. Invent nothing. If it did not happen in this session, it is not written.

Show me what you intend to write before writing it.
```

### `/morf:why`

```markdown
Take me back to the conversation a line came from.

The argument is a fragment of an observation, an article or a rule.

1. Find it across `.morf/`, including `dropped.md`, in fact
   articles, in `.morf/Rules/map.md` and in `.morf/Rules/**/*.log.md`.
   Say where it lives.
2. For each source, run:
   `python3 "$CLAUDE_PROJECT_DIR/.morf/scripts/read-session.py" <ref> <keyword>`
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

1. Read `.morf/dropped.md` — entries displaced within the
   last hundred sessions — and every line added since the `last` session id
   recorded in `.morf/audit.md`.

2. Compare them by meaning, not by wording. Report pairs where something
   displaced earlier was written down again as a new observation.

   Same thing, same words -> the displacement threshold is too low.
   Same thing, different words -> the wording is unstable, and one
   observation is being recorded twice under two names.

3. Count and report, without interpreting: lines added, promoted, displaced;
   lines that became rules and lines that became facts; lines sitting at
   the top level for over three periods without an exit; whether `dropped.md`
   grows faster than the levels.

4. Append the result to `.morf/audit.md` with the current session id
   as the new `last`. Keep previous entries — this file is a history.

Say plainly if there is nothing to report. A quiet audit is a good result.
```

## The `CLAUDE.md` next to MORF

The installer creates this file if it is missing and keeps the `Language`
section between markers, so a repeat install replaces only that section. It
writes the title, the two lines under it and that section — the `Never` list
below is an example to add yourself. The rest is yours; the working order
itself lives in the plugin's `morf` skill.

```markdown
# Notes

Memory lives in `.morf`, fact articles in `.morf/Facts`.
The working order is in the `morf` skill.

## Never

- Do not touch `[S= R= t=]` by hand: `score-memory.py` writes them.
- Do not edit `TAGS.md`, `INDEX.md`, `sessions.md`, `levels.md`: generated.
- Never write to or delete from `.morf/Transcripts`.
- Delete nothing else either. Displaced lines go to `dropped.md` with sources.

<!-- morf:language -->
## Language

Imperatives in English: instructions, commands, rules, agent definitions.
Everything in the indicative — observations, fact articles and replies to me
— in Russian.
<!-- /morf:language -->
```
