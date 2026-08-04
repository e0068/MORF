Audit the memory of the current project. Change nothing: report only.

1. Read `Claude/Memory/<project>/dropped.md` — entries displaced within the
   last hundred sessions — and every line added since the `last` session id
   recorded in `Claude/Memory/audit.md`.

2. Compare them by meaning, not by wording. Report pairs where something
   displaced earlier was written down again as a new observation.

   Same thing, same words -> the displacement threshold is too low.
   Same thing, different words -> the wording is unstable, and one
   observation is being recorded twice under two names.

3. Count and report, without interpreting: lines added, promoted, displaced;
   lines that became rules and lines that became knowledge; lines sitting at
   the top level for over three periods without an exit; whether `dropped.md`
   grows faster than the levels.

4. Append the result to `Claude/Memory/audit.md` with the current session id
   as the new `last`. Keep previous entries — this file is a history.

Say plainly if there is nothing to report. A quiet audit is a good result.
