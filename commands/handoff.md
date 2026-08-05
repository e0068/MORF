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
   If a rule received a `miss` or an `inverse`, it leaves the rule layer in
   this same session: its counters go up in `MORF/Rules/map.md`, the move is
   written into that file's `*.log.md` as `returned:`, and the line goes back
   to `L0` with its counters, sources and move history. Tell me at once.

3. Unexpected outcomes become a new line in `MORF/Memory/<project>/L0.md`:
   `- hit:1 use:0 <what happened> (s:<ref>)`
   Write it in the indicative, in the language set in CLAUDE.md.
   An observation is what occurred.

4. If a conclusion about how to act formed during the work, do not discard it.
   Record the observation in the indicative, mark it `↑`, and attach the
   proposed rule wording below it, in English.

5. Invent nothing. If it did not happen in this session, it is not written.

Show me what you intend to write before writing it.
