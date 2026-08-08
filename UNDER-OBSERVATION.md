# Under Observation

Changes that shipped **before both the reviewer and the tester reported
SATISFIED**. Each record stays here until observation confirms the change solved
its problem — or until it is reverted. One record per change; newest first.

A record is a database row: problem, solution, variants already tried and why
they failed, the date the problem was established, and the date/time of rollout.

---

## The observation gate read the session's folder as the commit's folder

- **Problem established:** 2026-08-08
- **Rolled out:** 2026-08-08 — same commit as the drop-in change below
- **Review / test:** author-tested only (five cases over `commit_dir`, all
  passing); **no reviewer, no independent test**. → under observation.

**Problem.** `gate-observation.py` took `cwd` from the hook event — the session's
folder — and asked *that* folder whether an Under Observation entry was staged.
The two are the same until they are not: this very commit was made in the main
checkout from a session living in one of its worktrees, so the ledger was staged
where the commit ran while the gate questioned the worktree, found nothing, and
blocked. An honest entry could not clear the gate at all, and the only ways past
it were to fake a verdict or to stage a decoy in the worktree.

**Solution.** `commit_dir(command, cwd)` reads the destination out of the command
that is about to run — `git -C <dir>`, or a `cd <dir>` ahead of it — resolving a
relative path against the session and falling back to the session only when the
command names nowhere else.

**Of a piece with the change it was blocking.** This is the same defect the whole
drop-in change removes, and the same one the memory's top level now states: a
stand-in that resembles the thing is not the thing, and it fails silently in both
directions. Two others of the family surfaced in the same minute — the gate also
fired on a *test command* whose text merely contained the words `git commit`,
judging a call by the text it carries rather than by what it does. That one is
left alone: it is the archive guard's known trade-off, deliberately blunt.

**What observation must confirm.** That commits from a worktree into a main
checkout now clear the gate on a staged ledger, and that no ordinary in-place
commit stopped being gated by the change.

---

## Drop-in `.morf` — MORF lives inside the repository, not in a central store

- **Problem established:** 2026-08-07
- **Rolled out:** 2026-08-08 — commit; installed into `Documents/Claude/MORF`
- **Review / test:** the core script change → `code-reviewer` **SATISFIED** (33
  tests, and the reviewer independently reverted `home()` to confirm the three new
  tests actually gate it). The integration pass → **NOT SATISFIED**: three findings
  (stale install instructions in `README.md`/`README.ru.md`/`docs/ru/установка.md`;
  `build-release.py` falsely claiming byte-reproducibility; a phantom
  `.morf/commands` in two comments). All three were fixed and verified — two
  consecutive builds now compare byte-identical — but **the fixes were verified by
  the agent that made them**, with no independent re-review, and **no test suite
  covers the installer end to end** (only manual scratch-repo runs). → under
  observation.

**Problem.** Memory was central: one store, `Memory/<project>/…`, and every session
had to be *attributed* to a project. That attribution was the most fragile part of
the system — it produced phantom shelves for every worktree, a consolidation debt
computed against an empty project, an audit timer ticking on registrations rather
than material, and a `t=0.0` time scale on the most-confirmed line in the store.
Separately, the code shipped as a plugin copied into `~/.claude/skills/morf`, so
edits in the repository and the running copy drifted apart silently.

**Solution.** MORF becomes a self-contained `.morf/` dropped into a repository —
code, hooks, commands, skill and memory together. `home()` is the `.morf` the
running script lives in (`__file__`), so there is nothing to resolve; a worktree
falls back to the main checkout's `.morf` via `git rev-parse --git-common-dir`. The
`<project>` path dimension collapses: one repo is one memory. The whole
recorded-judgment resolver is deleted. Drift dies by construction, because there is
no second copy. Install is `tools/install.sh`, which wires the hooks into the
repo's own `.claude/settings.json`, registers `/morf:*` under `.claude/commands/morf/`
and the skill under `.claude/skills/morf/`, and ignores the memory data (not the
code) in `.gitignore` — a worktree needs the scripts present for its hooks to fire.

**Tried and rejected.** Co-location was weighed and *rejected* on 2026-08-05 —
closer to an accidental commit and to `git clean`, and the supra-project layer
(Facts, Rules, audit, slot state) would be homeless. It was taken up now because a
consideration that rejection never examined turned it around: with memory inside the
repo, the git root answers the attribution question outright, so the fragile
resolver disappears rather than being repaired. The owner accepted the remaining
costs explicitly — no shared memory across projects (merge by hand if ever wanted),
and Obsidian simply reads the folder above the repositories. A flag-gated rollout
and dual-read were considered and dropped as needless operations.

**What observation must confirm.** That a fresh install works in a repo nobody
prepared by hand; that no phantom shelf ever appears again; that a worktree session
writes to the main checkout's `.morf`; and that the machinery, now vendored per
repository, does not start drifting between projects the way the central copy did —
the cost the owner accepted when choosing drop-in over a shared install.

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
