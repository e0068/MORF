# Deprecated — MORF is no longer a plugin

MORF moved from a central plugin installed into `~/.claude` to a self-contained
`.morf/` folder dropped inside each repository (code and data together). The
installer is now `tools/install.sh` (or the self-extracting `dist/install-morf.sh`
built by `tools/build-release.py`), which lays down `.morf/` and wires the hooks
into the repo's own `.claude/settings.json`.

`plugin.json` and `marketplace.json` are retained only so an earlier
`/plugin install morf@morf` can still be located and uninstalled. They are no
longer part of how MORF is installed or run and can be removed once no one has
the old plugin copy.

The hook wiring these manifests used to carry now lives in `hooks/hooks.json`,
which the installer reads as the canonical hook list and translates into project
settings (`${CLAUDE_PLUGIN_ROOT}/scripts/X.py` → `$CLAUDE_PROJECT_DIR/.morf/scripts/X.py`).
