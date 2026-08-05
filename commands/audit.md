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
   lines that became rules and lines that became facts; lines sitting at
   the top level for over three periods without an exit; whether `dropped.md`
   grows faster than the levels.

4. The balancer. The counts above are the flow's vital signs. Read them
   against the coefficients in `config.json` and report which way to move them
   so the flow stays present and varied — change nothing here, name only the
   direction.

   Stalling -> top level held past three periods, `dropped.md` flat, little
   promoted: the level limits and the rule-exit thresholds (`rulesOutByMiss`,
   `rulesOutByInverse`) are too slack, nothing leaves and the memory sets.
   Churning -> `dropped.md` outgrows the levels, or a displaced line returns
   (step 2): the thresholds are too tight, nothing lives long enough to mature
   and variety collapses to whatever was written last.

   The target is a live, varied flow, not a full upper level. Name the
   coefficient and the direction; the owner sets the number.

5. Append the result to `MORF/Memory/audit.md` with the current session id
   as the new `last`. Keep previous entries — this file is a history.

Say plainly if there is nothing to report. A quiet audit is a good result.
