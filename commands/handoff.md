Reconcile what happened with what the system predicted.

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/archive-session.py --handoff`.
   It copies the transcript into the archive and prints a reference to the
   stretch written since the previous call: `s:260803-a41f#412-980`.
   Use that reference as the source for every line you write below.
   If the session start reported an unfinished stretch, use its reference
   instead — the copy for it is already archived.

   Then record which project this session feeds:
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/archive-session.py --project <name>`.
   The folder you run in is a slot, not the project — a worktree feeds the
   project it is work on, not one named after the task. This is the shelf you
   write the lines below onto; naming it here is what makes the debt, the
   scale and the notice find the same project you did.

2. Expected outcomes are counters on existing lines; add no new lines for them:
   `hit` the prediction held · `use` the line changed what you did ·
   `miss` the prediction did not hold · `inverse` the opposite happened.

   Credit a `hit` or `use` only for a line that acted independently of your
   reading it. A line you loaded at start, quoted, or built on this session is
   suspect: a fresh confirmation may be your own attention echoing back. Credit
   it only when the situation held or the decision turned on it on its own
   terms; in doubt, leave the counter and name the line in the observation.

   `inverse` also creates a new line: the opposite is itself unexpected.
   A refutation matters more than a new finding — never skip it for brevity.
   If a rule received a `miss` or an `inverse`, it leaves the rule layer in
   this same session: its counters go up in `MORF/Rules/map.md`, the move is
   written into that file's `*.log.md` as `returned:`, and the line goes back
   to `L0` with its counters, sources and move history. Tell me at once.

3. Unexpected outcomes become a new line in `MORF/Memory/<project>/L0.md`:
   `- hit:1 use:0 <what happened> (s:<ref>)`
   Write it in the indicative, in the language set in CLAUDE.md.
   An observation is what occurred.

   But first make sure it is unexpected: grep the thought across `L1`, `L2`
   and `L3`. If memory already holds it, a subagent may have read that line
   back into the session — read back, its own words look like a fresh event.
   A match is at most a `hit` on the line that already carries it (step 2),
   and only if the situation itself recurred; never a second line saying
   what memory already holds.

4. If a conclusion about how to act formed during the work, do not discard it.
   Record the observation in the indicative, mark it `↑`, and attach the
   proposed rule wording below it, in English.

5. A fact article that took part in a decision gets `applied` raised in its
   front matter — the same event `use` records for an observation. If it is
   being applied again, return the line it came from to `L0.md` whole: same
   wording, same counters, same sources. A new line would be a forgery, and
   `/morf:why` has to lead back to the same conversations.

6. Fill the `about` column of this session's row in `MORF/Memory/sessions.md`:
   two or three words on what the work was about. The hook writes the row
   before the work starts and cannot know that.

7. Invent nothing. If it did not happen in this session, it is not written.

Show me what you intend to write before writing it.
