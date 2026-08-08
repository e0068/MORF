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
