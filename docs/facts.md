---
type: doc
description: the fact layer — the third exit, the article, scope, access, return; how it works and why
tags: [morf, facts]
---

# Facts

**EN** — [RU](ru/факты.md)

**What this is.** Articles about phenomena: true, repeatable, and yielding no action. Not one fact per file but one subject per file — "Shader cache", not "a cold cache makes the build take 40 seconds". Observations become its paragraphs.

**What for.** The third exit from memory. Without it an observation that is true and leads nowhere would decay together with the unconfirmed ones — the system would systematically discard what is true.

---

## How a fact appears

**How it works.** The verdict tries to state an imperative from an observation. If "do it this way" does not follow from the content — however much accumulates — the observation goes into facts.

It does not go as a separate file. First `TAGS.md` and `INDEX.md` are searched for an article about the same phenomenon: found, and the observation is appended as a section with its own sources; not found, and a new article is started. Related phenomena are joined with `[[...]]` links.

The same agent that makes the verdict appends the article. It must not duplicate: if a paragraph already covers this, only a new `s:` is added to it, while a new section is started for a new facet of the phenomenon. The rule is the one used for observations: a repeat raises a counter rather than breeding a record.

**Why this way.** The signal is a property of the content, not a deadline. From "compilation is slow" no imperative follows in principle, and waiting for one is pointless.

An article rather than a note per fact, because knowledge about a subject is assembled from many observations, and separately they are useless. "The cache is invalidated by the hash of the defines", "warm-up takes 40 seconds", "the release build behaves differently" — three files, none of which answers any question in full. One article does.

Links between phenomena do what tags cannot: a tag says "about the same thing", a link says "from here it follows to there". A map search finds the entrance, and from there the agent walks the links, wiki-style.

**Why not otherwise.** An early version said "high `S`, three periods without turning imperative". Three periods were a crutch standing in for an honest check: the verdict already tries to state an imperative on every consolidation, and the result of the attempt is a direct answer rather than an indirect sign.

The same version created a file per observation. Over a year that is thousands of one-line notes, impossible to read or maintain, and the map made of them stops narrowing anything: every query returns twenty nearly identical rows.

---

## The article

**How it works.**

```markdown
---
type: fact
description: how the shader cache works and when it misses
tags: [glsl, performance]
scope: [shader-lab]
applied: 3
---

# Shader cache

## Invalidation
The key includes the hash of the defines, so changing any define
wipes the cache entirely. (s:260731-9c2e#12-88)

Related: [[Build defines]], [[Warm-up on start]]

## Cold start
The first build takes about forty seconds. (s:260803-a41f#412-980)
```

**Why this way.** `description` is not decoration. The map is built from it, and the agent decides from it whether to open the file. Write it as the answer to "in what case will I need this". An article without a description is invisible to the system: nobody opens a file at random.

Sources are inherited from the original line. Without that, traceability breaks exactly here: the fact exists, its origin does not. `/morf:why` must work on an article the same way it works on a memory line.

`applied` counts how many times the article took part in decisions; `/morf:handoff` marks it the same way it marks `use` on observations.

**Why not otherwise.** The counter of articles without a description is printed by the script on every build — it is the list of what fell out of the system, not a decoration either.

---

## scope

**How it works.** A front-matter field listing the projects where the fact was established and where it certainly applies. It goes into the tag dictionary alongside the tags and narrows the results.

An article with a foreign `scope` is not excluded from search: if it surfaced by tag and fitted, the list is extended. Once the list reaches a second project, the fact is effectively general and the mark can go.

**Why this way.** There is one store of facts, and `scope` works as a ranking hint, not a wall. Place decides nothing for a fact: it is found by search, not by path.

**Why not otherwise.** Filing facts into contours physically would mean moving an article every time it turns out to be about the platform rather than the product — breaking links and tearing history. As a field it is one word to edit, and consolidation can do it by itself.

For rules it is the exact opposite: there the contour is a file, the moment of loading depends on it, and a rule is either here or everywhere. A file "for these two projects" does not exist.

---

## Access

**How it works.** Two hops: `MORF/Memory/TAGS.md` → the relevant part of `INDEX.md` → 2–5 articles. Both indexes are generated by `build-index.py`.

**Why this way.** Facts are the only layer that never reaches the agent on its own: observations are read at start, rules are loaded by the mechanism, facts have to be found. Both indexes exist for this layer.

The first hop is needed because the map grows with the collection and at a few hundred articles becomes expensive reading in its own right. The tag dictionary barely grows: tags run out sooner than articles.

**A tag is an axis of search, not a topic.** What the article is about is stated by its title; a tag exists to narrow the map. Hence the working criterion: **a tag earns its place when at least two articles carry it.** A tag on a single article narrows nothing and merely repeats the title — `build-index.py` lists such tags on every build.

Two to four tags per article: the subject (`glsl`, `cache`) and the facet (`performance`, `tooling`). What the title and description already say is not duplicated as a tag.

**The dictionary is closed.** A tag missing from `TAGS.md` does not exist; the agent proposes adding one but never invents. Otherwise within half a year `glsl`, `shader`, `shaders` and `graphics` pile up for the same thing and the first hop stops narrowing.

**Path check.** A folder name states its relation to its parent, not a standalone label. A path is read bottom-up as a phrase: `MORF/Memory/Transcripts/<id>` reads as transcripts of Claude's memory and holds together; `MORF/Memory/Memory` would read as "memory of memory" and does not. `build-index.py` reports repeated names on every build. The same test catches the opposite mistake — a level that adds nothing, like `Projects/shader-lab/project.md`.

**Why not otherwise.** Dataview does the same thing live and prettier, but its queries only run inside the editor: an agent reading the file sees the query text, not the result. Materialised indexes are for the agent, plugins stay for you, and they do not interfere.

Vector search is not worth setting up below a few thousand articles: it answers "here are similar chunks of text", while the agent needs "here is the map of what exists, open the third item". The second is done with a plain markdown file and works more reliably, because it does not hallucinate relevance.

---

## Return to observations

**How it works.** When `applied` grows, the same line returns to `L0.md` with its own counters and sources.

**Why this way.** Without a return the exit into facts would be a trap: the article lives forever, gathers no counters, and never becomes a rule however much everyone leans on it.

The same line returns, not a new one: it is the same thought, and `/morf:why` must lead to the same conversations. Declaring it new would be a forgery.

It did not go stale while it lay there, because the clock was stopped: decay is counted in opportunities to apply, and while the subject never came up there were none.

A separate case is a fact that produced an action: "since compilation is slow, we now build incrementally". That is not a return but a candidate rule outright — the wording turned imperative.

**Why not otherwise.** An early version returned a fact as a new line with zero counters so that old dates would not extinguish it immediately. That was a workaround for a defect in the calculation: under calendar decay a returning line really would zero out by age — and so would any rarely applied observation. Fixing the return fixed the main scale as well.

The same version marked an article that had gone back and forth twice as settled and never opened it again. A crutch against oscillation, and the oscillation was produced by that same false decay. With the right clock it is unnecessary.
