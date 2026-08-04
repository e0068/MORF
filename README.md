# MORF

**M**emory **o**f **O**bservations, **R**ules and **F**acts.

The order of the letters is the priority of exits, not the flow. An observation
is made for the sake of a rule: a rule is the main exit, and the whole queue
exists for it. Facts are the side exit, for what yields no action.

The flow runs the other way: observations → facts → rules. Everything is
traceable down to the raw conversation and stored as plain markdown files —
any editor will do, and Obsidian is convenient for the canvas.

[По-русски](README.ru.md)

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

The model is on the canvas at `Claude/Memory/model.canvas`, the reasoning is
in [`Claude/Docs/`](docs/readme.md).

## Three categories

| | What it is | Mood |
|---|---|---|
| **Observation** | what happened and was unexpected | indicative |
| **Fact** | an article about a phenomenon that yields no action | indicative |
| **Rule** | how we act from now on | imperative |

Memory is a queue of candidate rules. An observation either matures into a
rule, or turns out to be a fact, or decays — and no outcome is silent.

## License

MIT.
