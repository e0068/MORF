Show what moved in memory, as a matrix read from disk rather than a claim.

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/trace.py --show` and show me its
   output as it comes — a markdown table, one row per shelf, one column per
   level. The point of the matrix is that it is the disk, not your account of
   it: add nothing, drop nothing, restate nothing.

2. Read a cell as `count (+in −out)`: the standing count at the round's end, and
   in brackets what the round added and took away. A bare number is a cell that
   did not move. `Facts` and `Rules` ride the same table as their own rows — a
   count and, when it changes, `(+in −out)`.

3. In `Memory/TRACE.md` the cell is split into clicks, so open that note in
   Obsidian: the **count** links to the level's own file (the whole list), the
   **`(+in −out)`** to a heading that names exactly what arrived (`←`) and left
   (`→`) this round, and the **name** to the shelf's inbox file. `TRACE.md` is
   generated; never edit it.

4. `--show` renders whether or not anything moved. The same render prints itself
   on `Stop` when — and only when — something moved, so a turn that changed no
   memory says nothing.

Movement is derived from a baseline taken once at the start of the session, so
the matrix spans the whole round; a line survives a promotion because it keeps
its text and its sources across the move, and a fact or rule is tracked by the
same identity. What the memory *owes* — unread stretches, consolidation, the
audit — is a separate readout: `due.py`.
