# MORF

**English** · [Русский](README.ru.md)

**M**emory **o**f **O**bservations, **R**ules and **F**acts — three-phase
memory for Claude.

At the end of a piece of work the agent writes down what happened and was
unexpected. Those observations pile up, get scored, and are consolidated level
by level. What matures into "do it this way" becomes a rule and starts loading
in every session. What stays true but yields no action settles as an article
about the phenomenon. What stops being confirmed and used is displaced, with
its sources intact.

Every line keeps a reference to the stretch of conversation it came from, so
any of it can be traced back and disputed. Everything is stored as plain
markdown files: any editor will do, and Obsidian is convenient for the canvas.

## Install

Download `Install-MORF.command` from the release and double-click it. It asks for the vault
folder, the name of the first project and the language for observations and
fact articles, drops the plugin into
`~/.claude/skills/` and lays the files out in the vault. No terminal, no
permission prompts.

On first launch macOS warns about an unsigned file: right-click → Open → Open.

Through the marketplace, if you prefer:

```
/plugin marketplace add e0068/MORF
/plugin install morf@morf
```

## What is inside

| Part | What it does |
|---|---|
| hook `SessionStart` | registers the session, sweeps in cut-short transcripts, reports the unprocessed stretch |
| hook `PreToolUse` | keeps tools out of the conversation archive |
| `/morf:handoff` | reconciliation at the end of a piece of work: transcript copy, counters, new observations |
| `/morf:why` | from a line back to the conversation it came from |
| `/morf:audit` | threshold review every tenth session of the project |
| skill `morf` | what to read at session start, how to consolidate, where things go |

The model is on the canvas at `MORF/Memory/model.canvas`, the reasoning is
in [`MORF/Docs/`](docs/readme.md).

## Three categories

| | What it is | Mood | Access |
|---|---|---|---|
| **Observation** | what happened and was unexpected | indicative | fast: read at session start |
| **Fact** | an article about a phenomenon that yields no action | indicative | slow: found by search |
| **Rule** | how we act from now on | imperative | fast: loaded by the mechanism |

Observations and rules arrive on their own, so they have to stay small — the
context is finite. Facts may be any number, because nothing loads them until
somebody looks: `TAGS.md` narrows the map, `INDEX.md` points at the articles.
That is why the fact layer has indexes and the other two do not.

Memory is a queue of candidate rules. An observation either matures into a
rule, or turns out to be a fact, or decays — and no outcome is silent.

## Three axes

Each axis pairs up two of the three, and no pair repeats.

| Axis | Observations | Facts | Rules |
|---|---|---|---|
| **Mood** | indicative | indicative | imperative |
| **Access** | fast | slow | fast |
| **Persistence** | transient | persistent | persistent |

Observations and facts meet on mood, observations and rules on access, facts
and rules on persistence. Every pair shares exactly one axis, and no two
entities match on all three.

The axes are not decoration: each one drives a mechanism. Mood is what the
intake filter checks. Access decides who needs indexes — only the slow layer
does. Persistence decides who decays: an observation exists to be
resolved into a rule, a fact or `dropped`, and stops existing once it is, while
a fact and a rule are outcomes that stand until disproven.

## License

MIT.
