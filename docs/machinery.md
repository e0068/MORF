---
type: doc
description: the operational machinery — hooks, triggers, agent tasks and debts, and why enforcement arrives every turn rather than blocking once
tags: [morf, hooks]
---

# Machinery

**EN** — [RU](ru/машинерия.md)

The model is a set of files; what keeps them moving is machinery that runs without being asked. It divides in two, and the division is the whole of this note. **⬜ machinery** fires on a Claude Code event, establishes only what can be established mechanically, and interprets nothing. **🟩🟦🟪 work** needs a reading of evidence — what happened, what it is worth, whether a rule holds — so it is left to an agent, never to a script. A script that guessed the weight of a case would be a self-report dressed as a fact, and a self-report is the one thing this system refuses to trust.

The machinery raises **debts** the agent owes, and stands **guard** where a single write could corrupt the record. The two are not the same pressure: a debt is discharged by writing something into the memory, a guard is a wall that a call bounces off. What follows is the wiring, ground truth in `hooks/hooks.json`; the installer translates it into a repo's own `.claude/settings.json`, rewriting `${CLAUDE_PLUGIN_ROOT}/scripts/X.py` into `$CLAUDE_PROJECT_DIR/.morf/scripts/X.py`, matchers and timeouts preserved.

## Hooks

Six wirings, on five Claude Code events. Every one either records a fact, prints an instruction the agent reads, or blocks a call — none interprets.

| Event | Script(s) | What it does |
|---|---|---|
| `SessionStart` | `archive-session.py` · `trace.py --mark` | registers the session as a row in `sessions.md` and in the folder's `.state` index; on first sight creates the level files; sweeps in the transcripts of sessions that ended without a handoff and names their unread stretches; prints the inbox count and every owed debt. Then snapshots the whole of memory as the baseline against which movement is measured. |
| `SessionEnd` | `archive-session.py --ended` | marks the session over in `.state`, so its tail can be swept in safely instead of guessed at by how long its transcript has been silent. |
| `UserPromptSubmit` | `due.py --prompt` | prints what the memory owes — on **every** turn, not once at the start. |
| `PreToolUse` `Write\|Edit\|MultiEdit\|NotebookEdit\|Bash` | `guard-archive.py` · `guard-rules.py` | blocks a write or a shell deletion landing inside the conversation archive; blocks an edit to a watched rule file that has drifted outside MORF and not been accounted for. |
| `PreToolUse` `Bash` | `gate-observation.py` | blocks a `git commit` that carries neither a recorded reviewer-and-tester pass nor a staged `UNDER-OBSERVATION.md` entry. |
| `Stop` | `trace.py --report` · `due.py --stop` | shows what moved this turn, if anything did; then refuses to let the turn end while a debt still stands. |

**Why the archive is filled by a hook and defended by one.** `SessionStart` copies transcripts out of Claude Code's own store into `.morf/Transcripts` — a permanent copy, because Claude Code's history expires and a memory that points at an expiring store is not a memory. The copy is the one path in, so `guard-archive.py` treats any *tool* touching the archive as either a mistake or an attempt to erase evidence, and does not bother telling them apart. It judges a write by where it lands, never by what it says — matching the payload once blocked editing the very instructions that merely *name* the archive path.

**Why `trace` is derived and not written.** A trace the agent narrates would be a claim; instead `--mark` photographs memory at the start and `--report` diffs the disk at the end, so a line counts as moved only because it now sits in a different file. Identity is `(text, sources)` hashed, which survives every promotion, return and drop, so the two readings tell — per level — what arrived and what left.

## Triggers

Three kinds of thing set the machinery in motion. Keeping them apart matters, because they are answered in different places and one of them must never bill the human.

**Events** drive the hooks above: session start and end, every prompt, every tool call, every turn-stop, and a `git commit` caught as a `Bash` call.

**Computed debts** are derived by `due.py` from what already lies on disk — nothing new is bookkept, because a separate ledger would be a second copy that goes stale. It surfaces them on `--prompt` and `--stop`:

| Debt | Condition |
|---|---|
| handoff | a stretch this folder archived is not yet written up as observations — the memory does not name it as a source. |
| consolidation `L→L+1` | a lower level cites a session the upper has never *considered*, **and** the level's horizon has passed — `L1` after 1 session, `L2` after 5, `L3` after 25 (`base · step^i`). |
| audit | ten or more sessions since the id recorded in `audit.md`'s `last`. |
| facts-map-stale | a `Facts` article is newer than `INDEX.md`, so it is invisible to search until the map is rebuilt. |
| inbox-full | `L0` holds at its limit (40) — past it, each new observation displaces an earlier one. |
| rules-drift | a watched rule file changed outside MORF and its lines are unaccounted, or its log cannot be read back. |

The subtlety in consolidation is the word *considered*: a level has **seen** the sessions its lines cite plus the ones it weighed and declined on a `<!-- considered: … -->` line. A decline is an outcome, and it closes the debt exactly as a promotion does — so the upper level counts it as seen, and the lower must not re-offer it as material.

**Guards** fire on the attempt itself, at `PreToolUse`, and are answered by a block rather than a debt: a write or deletion inside the archive → `guard-archive.py`; an edit over unaccounted foreign drift in a watched rule file → `guard-rules.py`; a commit without verdicts → `gate-observation.py`. The guard is needed precisely where a debt is too late — once two edits mix, telling whose is whose is impossible afterward.

## Tasks for agents

Where judgment is required, the colour of the arrow on the canvas names who acts, because the same steps done from a different vantage give a different answer.

| | Executor | The work |
|---|---|---|
| 🟩 | agent inside a task | notices the unexpected and runs `/morf:handoff`: archive the stretch, reconcile prediction against outcome (`hit`/`use`/`miss`/`inverse`), write new `L0` observations, mark the mature one `↑` with a drafted rule, bump the `applied` count of any fact it used, and fill the session's `about`. |
| 🟦 | agent at session start | consolidates a level — score, cluster, attempt one imperative, then rule / leave / fact / dropped; a promotion displaces the weakest by `S`; the verdict is written as a `<!-- considered: … -->` line naming what was weighed. Runs `/morf:audit` every tenth session (compare displaced against rewritten, report only). Writes fact articles (find via `TAGS → INDEX`, append a section, `[[link]]`). Adopts rules (`rules.py --track` / `--adopt`) and discharges drift (`rules.py --diff` → log → `--seal`). |
| 🟪 | reviewer | runs a candidate rule against recent diffs before adoption — the way to judge a rule without knowing the subject: by its consequences, not its wording. |
| — | any agent, on demand | `/morf:why` walks a line back through `read-session.py` to the raw conversation; `/morf:trace` shows the `trace.py --show` matrix. |
| 🟥 | you | the one transition a script may not make: approving and installing a hook — moving a rule into enforcement. |

Green and blue are the same mechanism in different context. Wording gains from the agent being inside the task and seeing the detail; the decision suffers from it, because a fresh successful case weighs more than the rest simply by being in view.

## Debts

A debt is the agent's, never the owner's to be asked about — *I am not the timer, and I am not the one who forgot.* `due.py` derives every debt from disk, it arrives on every turn (`--prompt`), and `--stop` refuses to end a turn while one stands: discharge it, or say plainly in the answer that you are leaving it and why. The kinds are the computed debts tabled above — handoff, consolidation `L→L+1`, audit, facts-map-stale, inbox-full, rules-drift.

**A debt clears by appearing in the memory.** A handed-off stretch names itself as a source `(s:ref)`; consolidation writes the `<!-- considered: … -->` line naming the sessions weighed — and *considered and declined is itself an outcome that is written down*, closing the debt the same as a promotion would; an audit writes a new `last`; a stale map is rebuilt. There is no separate "done" flag, on purpose: an unwritten decision is indistinguishable from work never done, so the only way to mark a debt paid is to leave the evidence of paying it.

**Why the enforcement does not bill the human.** The pressure is in *arriving every turn*, not in blocking once at the start — a notice said only at session start is read past, because the turn ends however it likes regardless. `Stop` is the single point where the answer is already written and the debt still stands, so it sends the turn back; `stop_hook_active` marks a turn already returned once, so it is not blocked twice — a second block would be a hang, not pressure. And the debt hook exits 0 and writes to **stdout**, reaching the agent as an instruction, rather than exiting 2 and discarding the prompt the human just typed. Enforcement that makes a person retype their prompt to pay for what an agent forgot is worse than no enforcement at all: it teaches them to remove the hook.
