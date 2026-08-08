#!/bin/sh
# MORF installer — drops a self-contained `.morf/` into a repository.
#
# MORF is no longer a central plugin. The scripts and the memory they tend live
# together in one `.morf/` folder inside the repo: nothing to point at, nothing
# to configure. This script lays that folder down and wires the hooks into the
# repo's own `.claude/settings.json`.
#
#   tools/install.sh                 install into the git top-level of the cwd
#   tools/install.sh <target-repo>   install into that repository
#   tools/install.sh --lang German   set the content language non-interactively
#   tools/install.sh --private       let the whole `.morf` travel with the repo
#                                     (skip the .gitignore step that ignores data)
#
# Care carried over from the old installer: memory records are never touched —
# only what is missing is created — and a code file this run replaces is kept
# alongside with a timestamped `.bak`. No dependency beyond python3.

set -eu

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
}

# ===== Where the payload sits =====
# Two layouts: run from the repo as `tools/install.sh`, the source dirs are one
# level up; run from a self-extracted bundle, `install.sh` sits beside them.

SELF=$(cd "$(dirname "$0")" && pwd)
if [ -d "$SELF/scripts" ]; then
  SRC="$SELF"
elif [ -d "$SELF/../scripts" ]; then
  SRC=$(cd "$SELF/.." && pwd)
else
  echo "install.sh: cannot find the MORF payload (no scripts/ beside me or above)." >&2
  exit 1
fi

# ===== Arguments =====

TARGET=""
LANGUAGE=""
PRIVATE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --private) PRIVATE=1 ;;
    --lang)
      shift
      [ $# -ge 1 ] || { echo "install.sh: --lang needs a value." >&2; exit 1; }
      LANGUAGE="$1" ;;
    --lang=*) LANGUAGE="${1#--lang=}" ;;
    -h|--help) usage; exit 0 ;;
    --) shift; break ;;
    -*) echo "install.sh: unknown option: $1" >&2; exit 1 ;;
    *) TARGET="$1" ;;
  esac
  shift
done
[ -n "${1:-}" ] && [ -z "$TARGET" ] && TARGET="$1"

# ===== The target repository =====
# Default: the git top-level of the current directory, or the cwd if not a repo.

if [ -z "$TARGET" ]; then
  TARGET=$(git -C "$(pwd)" rev-parse --show-toplevel 2>/dev/null || pwd)
fi
TARGET=$(cd "$TARGET" 2>/dev/null && pwd) || {
  echo "install.sh: target is not a directory: $TARGET" >&2
  exit 1
}

MORF="$TARGET/.morf"
STAMP=$(date +%y%m%d-%H%M)
PROJECT=$(basename "$TARGET")

# ===== Laying down the code =====
# Our files are updated in place; an edited one is kept beside it as a `.bak`.
# `place` runs in this shell — the copy loops read from files, not pipes — so a
# plain variable counts the replacements.

CHANGED=0
cleanup() { rm -f "${LIST:-}"; }
trap cleanup EXIT

place() {  # src dst — update in place, keep a .bak of an edited file
  src="$1"; dst="$2"
  if [ -f "$dst" ] && ! cmp -s "$src" "$dst"; then
    cp "$dst" "$dst.$STAMP.bak"
    CHANGED=$((CHANGED + 1))
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
}

# scripts/ hooks/ docs/ keep their subdir under `.morf/`. Commands do not: Claude
# Code registers project commands only from `.claude/commands/`, so they are laid
# down there separately, below.
# Redirect from a real file, not a pipe, so `place`'s counter runs in this shell.
LIST=$(mktemp)
for sub in scripts hooks docs; do
  [ -d "$SRC/$sub" ] || continue
  # Skip build litter: __pycache__, compiled python, .DS_Store.
  find "$SRC/$sub" -name __pycache__ -prune -o \
    -type f ! -name '*.pyc' ! -name '.DS_Store' -print >> "$LIST"
done
while IFS= read -r f; do
  rel=${f#"$SRC"/}
  place "$f" "$MORF/$rel"
done < "$LIST"

# The model canvas sits at the root of `.morf/`, as the docs describe it.
for c in "$SRC"/assets/*.canvas; do
  [ -f "$c" ] && place "$c" "$MORF/$(basename "$c")"
done

# ===== Registering the slash commands =====
# Claude Code registers a project command from `<repo>/.claude/commands/`, not
# from `.morf/`, and a subdirectory becomes the command's namespace:
# `.claude/commands/morf/handoff.md` is invoked as `/morf:handoff` (confirmed on
# Claude Code 2.1.222 — the bare `/handoff` does not resolve). So the command
# texts go under a `morf/` subdir there. Only that subdir is ours: a user's own
# `.claude/commands` are left untouched, and `place` keeps a `.bak` of an edited
# command, so a re-run is idempotent. The command bodies already invoke the
# scripts by their installed path (`$CLAUDE_PROJECT_DIR/.morf/scripts/X.py`), so
# they are copied verbatim.
if [ -d "$SRC/commands" ]; then
  for cmd in "$SRC"/commands/*.md; do
    [ -f "$cmd" ] || continue
    place "$cmd" "$TARGET/.claude/commands/morf/$(basename "$cmd")"
  done
fi

# ===== Registering the morf skill =====
# Claude Code registers a project skill from `<repo>/.claude/skills/<name>/SKILL.md`,
# and the skill's command is its directory name: `.claude/skills/morf/SKILL.md`
# loads as `/morf` (Claude Code skills docs, project-skill table:
# `.claude/skills/<skill-name>/SKILL.md`). So the root `SKILL.md` goes under a
# `morf/` subdir there. Only that subdir is ours: a user's own `.claude/skills`
# are left untouched, and `place` keeps a `.bak` of an edited SKILL.md, so a
# re-run is idempotent. The skill body already invokes the scripts by their
# installed path (`$CLAUDE_PROJECT_DIR/.morf/scripts/X.py`), so it is copied
# verbatim.
if [ -f "$SRC/SKILL.md" ]; then
  place "$SRC/SKILL.md" "$TARGET/.claude/skills/morf/SKILL.md"
fi

# ===== The memory skeleton (only where missing) =====
# Records are never overwritten. The running scripts create the same skeleton on
# first session; laying it down here means the folder reads as ready at once.

mkdir -p "$MORF/Observations" "$MORF/Transcripts" "$MORF/Facts" "$MORF/Rules" "$MORF/.state"

for level in L0 L1 L2 L3; do
  target="$MORF/Observations/$level.md"
  [ -f "$target" ] || printf -- '---\nname: %s-%s\n---\n\n' "$PROJECT" "$level" > "$target"
done
[ -f "$MORF/dropped.md" ] || printf -- '---\nname: %s-dropped\n---\n\n' "$PROJECT" > "$MORF/dropped.md"
[ -f "$MORF/sessions.md" ] || printf '| id | date | project | about |\n|---|---|---|---|\n' > "$MORF/sessions.md"
[ -f "$MORF/audit.md" ] || printf 'last: none\n\n' > "$MORF/audit.md"
# levels.md is generated by score-memory.py; it is not seeded here.

# ===== Wiring the hooks into the repo's settings =====
# The canonical hook list is `hooks/hooks.json`. It is translated, not
# hardcoded: `${CLAUDE_PLUGIN_ROOT}/scripts/X.py` becomes
# `"$CLAUDE_PROJECT_DIR/.morf/scripts/X.py"`, matchers and timeouts preserved.
# Existing user settings are merged, not clobbered; a re-run replaces only
# MORF's own groups, so it is idempotent.

SETTINGS="$TARGET/.claude/settings.json"
mkdir -p "$TARGET/.claude"
HOOKS_SRC="$SRC/hooks/hooks.json"
[ -f "$HOOKS_SRC" ] || { echo "install.sh: missing $HOOKS_SRC" >&2; exit 1; }

python3 - "$HOOKS_SRC" "$SETTINGS" <<'PY'
import json, re, sys
from pathlib import Path

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
MARK = "$CLAUDE_PROJECT_DIR/.morf/scripts/"

def translate(cmd: str) -> str:
    return re.sub(r"\$\{CLAUDE_PLUGIN_ROOT\}/(\S+\.py)",
                  r'"$CLAUDE_PROJECT_DIR/.morf/\1"', cmd)

wanted = json.loads(src.read_text(encoding="utf-8")).get("hooks", {})
for groups in wanted.values():
    for group in groups:
        for hook in group.get("hooks", []):
            if hook.get("type") == "command" and "command" in hook:
                hook["command"] = translate(hook["command"])

try:
    settings = json.loads(dst.read_text(encoding="utf-8"))
except (OSError, ValueError):
    settings = {}
settings.setdefault("hooks", {})

def ours(group) -> bool:
    return any(MARK in h.get("command", "") for h in group.get("hooks", []))

for event, groups in wanted.items():
    kept = [g for g in settings["hooks"].get(event, []) if not ours(g)]
    settings["hooks"][event] = kept + groups

dst.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY

# ===== .gitignore: ignore the data, keep the code committable =====
# A worktree must have `.morf/scripts` present for its hooks to fire, so the
# code is committed and only the memory data is ignored. `--private` skips this,
# letting the whole `.morf` — data and all — travel with the repo. Idempotent:
# the marked block is written once.

GITIGNORE="$TARGET/.gitignore"
MARK_START="# >>> morf (memory data; .morf/scripts,hooks,docs stay committed) >>>"
MARK_END="# <<< morf <<<"

if [ "$PRIVATE" -eq 0 ]; then
  if [ -f "$GITIGNORE" ] && grep -qF "$MARK_START" "$GITIGNORE"; then
    :   # already present
  else
    {
      printf '\n%s\n' "$MARK_START"
      printf '# A worktree needs .morf/scripts to fire its hooks, so code is committed and\n'
      printf '# only data is ignored. Re-run with --private to commit the whole .morf.\n'
      for entry in \
        .morf/Observations/ .morf/Transcripts/ .morf/Facts/ .morf/Rules/ \
        .morf/.state/ .morf/sessions.md .morf/audit.md .morf/levels.md \
        .morf/dropped.md .morf/INDEX.md .morf/TAGS.md .morf/TRACE.md; do
        printf '%s\n' "$entry"
      done
      printf '%s\n' "$MARK_END"
    } >> "$GITIGNORE"
  fi
fi

# ===== Language block in the target's CLAUDE.md =====
# The content language is an instruction to the agent, so it goes where
# instructions load by themselves: the repo's CLAUDE.md. Default from the
# system locale; `--lang <Name>` overrides it for non-interactive runs.
# Markers let a repeat install replace only this section.

LANGUAGES='sq:Albanian
am:Amharic
ar:Arabic
hy:Armenian
az:Azerbaijani
eu:Basque
be:Belarusian
bn:Bengali
bs:Bosnian
bg:Bulgarian
my:Burmese
ca:Catalan
zh:Chinese
hr:Croatian
cs:Czech
da:Danish
nl:Dutch
en:English
et:Estonian
fi:Finnish
fr:French
gl:Galician
ka:Georgian
de:German
el:Greek
gu:Gujarati
he:Hebrew
hi:Hindi
hu:Hungarian
is:Icelandic
id:Indonesian
ga:Irish
it:Italian
ja:Japanese
kn:Kannada
kk:Kazakh
km:Khmer
ko:Korean
ky:Kyrgyz
lo:Lao
lv:Latvian
lt:Lithuanian
mk:Macedonian
ms:Malay
ml:Malayalam
mt:Maltese
mr:Marathi
mn:Mongolian
ne:Nepali
no:Norwegian
fa:Persian
pl:Polish
pt:Portuguese
pa:Punjabi
ro:Romanian
ru:Russian
sr:Serbian
si:Sinhala
sk:Slovak
sl:Slovenian
so:Somali
es:Spanish
sw:Swahili
sv:Swedish
tl:Tagalog
tg:Tajik
ta:Tamil
te:Telugu
th:Thai
tr:Turkish
tk:Turkmen
uk:Ukrainian
ur:Urdu
uz:Uzbek
vi:Vietnamese
cy:Welsh
yi:Yiddish
zu:Zulu'

if [ -z "$LANGUAGE" ]; then
  code=${LANG:-}
  code=${code%%.*}      # en_US.UTF-8 -> en_US
  code=${code%%_*}      # en_US       -> en
  LANGUAGE=$(printf '%s\n' "$LANGUAGES" | grep "^$code:" | cut -d: -f2 || true)
  [ -z "$LANGUAGE" ] && LANGUAGE="English"
fi

CLAUDE_MD="$TARGET/CLAUDE.md"
BLOCK=$(printf '<!-- morf:language -->\n## Language\n\nImperatives in English: instructions, commands, rules, agent definitions.\nEverything in the indicative — observations, fact articles and replies to me\n— in %s.\n<!-- /morf:language -->' "$LANGUAGE")

if [ -f "$CLAUDE_MD" ] && grep -q '<!-- morf:language -->' "$CLAUDE_MD"; then
  python3 - "$CLAUDE_MD" "$BLOCK" <<'PY'
import re, sys
path, block = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
text = re.sub(r"<!-- morf:language -->.*?<!-- /morf:language -->", lambda _: block, text, flags=re.S)
open(path, "w", encoding="utf-8").write(text)
PY
elif [ -f "$CLAUDE_MD" ]; then
  printf '\n%s\n' "$BLOCK" >> "$CLAUDE_MD"
else
  printf '# Notes\n\nMemory lives in `.morf`, fact articles in `.morf/Facts`.\nThe working order is in the `morf` skill.\n\n%s\n' "$BLOCK" > "$CLAUDE_MD"
fi

# ===== Report =====

echo "MORF installed into: $MORF"
echo "  scripts, hooks, docs copied; memory skeleton created where missing."
echo "  hooks wired into: $SETTINGS"
echo "  commands registered as /morf:* in: $TARGET/.claude/commands/morf/"
echo "  skill registered as /morf in: $TARGET/.claude/skills/morf/SKILL.md"
if [ "$PRIVATE" -eq 0 ]; then
  echo "  .gitignore: memory data ignored, code committable (re-run --private to keep data too)."
else
  echo "  --private: .gitignore left untouched; the whole .morf travels with the repo."
fi
echo "  content language: $LANGUAGE (CLAUDE.md)"
[ "$CHANGED" -gt 0 ] && echo "  replaced $CHANGED edited code file(s); previous kept with the .$STAMP.bak suffix."
echo "Open Claude Code in $TARGET — the hooks fire on their own."
