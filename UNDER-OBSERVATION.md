# Under Observation

Changes that shipped **before both the reviewer and the tester reported
SATISFIED**. Each record stays here until observation confirms the change solved
its problem — or until it is reverted. One record per change; newest first.

A record is a database row: problem, solution, variants already tried and why
they failed, the date the problem was established, and the date/time of rollout.

---

## A′ — resolve a session's project by relation, not by folder-name proxy

- **Problem established:** 2026-08-05
- **Rolled out:** 2026-08-06 22:20 MSK — commit + merge to main + install to the live plugin
- **Review / test:** `code-reviewer` → SATISFIED. Tester → **NOT RUN** (no test
  suite fires the session boundary against the live vault yet; verified only on a
  copy). → under observation.

**Problem.** A session's project — which memory shelves, which session-scale, and
which debt it feeds — was resolved by the working-folder basename. For git
worktrees, the normal MORF-dev workflow, the folder is named after the task, so:

- the consolidation-debt hook checked an empty phantom project and never fired —
  consolidation ran ≈ once ever, leaving L0 a graveyard, Facts empty, L3 empty;
- `exposure_scale` filed a line's own sources under the wrong project and dropped
  them (`MORF/L2`'s sources sit under `Claude` → `t=0.0`, the temporal machinery
  dead on the vault's most-confirmed line).

**Solution.** `morf.project(cwd)` resolves by the relation, in order: (1) the
judgement the agent records at handoff into `.state/<slot>.json`; (2) a git seed
(a worktree is named by its main checkout); (3) the folder name; `—` for the vault
and home. Wired into `archive-session.py` (index column + `crowding` notice +
session-start debt) and `due.py`'s two hooks. `archive-session.py --project <name>`
persists the agent's judgement. Added: a handoff step to record it; a `use`/`hit`
hygiene rule (do not credit a line you merely read this session); the discharge
command named in `due.py`'s debt message; a backstop line in `~/.claude/CLAUDE.md`.

**Variants tried and rejected:**

- **Two pools (project + general observations, moved by hand):** the vault already
  rejected it (`docs/observations.md:84`) — it split weight into `hit:1` lines in
  two folders and the manual move never happened.
- **Crediting cross-project recurrences onto the home line:** `exposure_scale`
  drops foreign-project sources (`if m in scale`), so the scorer ignores the extra
  evidence — the score stays broken. A supra-project home is needed, not a bigger
  home-project line. (Left for a later change; not in this rollout.)
- **Pure git-basename resolution (option A):** still a proxy — breaks if the repo
  name ≠ the project name. Kept only as the seed; the recorded judgement overrides.

**How we will know it worked.** A worktree turn now surfaces MORF's `L0 → L1`
consolidation debt (verified on a vault copy: the hook printed it where the old
proxy printed nothing). Watch that consolidation actually runs, that L3 and Facts
begin to fill, and that re-scored MORF lines stop reading `t=0.0` once sessions are
filed under the project they feed.
