#!/bin/bash
# MORF installer. Three-phase memory for Claude. One double click and you are done.
#
# Drops the plugin into ~/.claude/skills, where Claude Code picks it up by
# itself: no marketplace, no install command, no permission prompt per step.
# The payload is embedded in this file; nothing else to download.
#
# It resolves earlier installs: a marketplace copy, a half-installed folder,
# a pointer to another MORF folder — it asks what to do with each of them.
# Memory records are never touched.

set -euo pipefail

SKILLS_DIR="$HOME/.claude/skills/morf"
PLUGINS_DIR="$HOME/.claude/plugins"
POINTER="$HOME/.claude/morf-path"
OLD_POINTER="$HOME/.claude/memory-vault"   # what versions before 1.3 wrote
STAMP=$(date +%y%m%d-%H%M)

# ===== Dialogs =====
# Messages are AppleScript source, so a quote or a backslash in a path or in
# what the owner typed would be a compile error, which `on error` cannot catch.
# Escape the substitutions only: the messages themselves rely on literal \n.

esc() {
  printf '%s' "$1" | sed 's/[\\"]/\\&/g'
}

say() {
  osascript -e "display dialog \"$1\" buttons {\"OK\"} default button 1 with title \"MORF\"" >/dev/null
}

fail() {
  osascript -e "display dialog \"$1\" buttons {\"Close\"} default button 1 with icon stop with title \"MORF\"" >/dev/null
  exit 1
}

pick() {  # question, button1, button2 -> prints the chosen one
  osascript -e "try
    button returned of (display dialog \"$1\" buttons {\"$2\", \"$3\"} default button 2 with title \"MORF\")
  on error
    return \"\"
  end try"
}

# ===== Earlier installs =====

resolve_marketplace() {
  local found
  found=$(find "$PLUGINS_DIR" -maxdepth 4 -type d -name "morf*" 2>/dev/null | head -1 || true)
  [ -z "$found" ] && return 0

  local answer
  answer=$(pick "A marketplace copy of the plugin is already installed.\n\nTwo copies expose the same commands, and which one wins is unpredictable. Remove the marketplace copy?" "Keep" "Remove")
  [ "$answer" != "Remove" ] && return 0

  if command -v claude >/dev/null 2>&1; then
    claude plugin uninstall morf@morf >/dev/null 2>&1 \
      || say "Removing via claude failed. Open Claude Code and run:\n\n/plugin uninstall morf@morf"
  else
    say "claude is not on PATH. Open Claude Code and run:\n\n/plugin uninstall morf@morf"
  fi
}

resolve_previous() {
  [ -d "$SKILLS_DIR" ] || return 0

  local answer
  if [ -f "$SKILLS_DIR/.claude-plugin/plugin.json" ]; then
    answer=$(pick "The plugin is already installed here. Update it to this version?" "Cancel" "Update")
  else
    answer=$(pick "A half-installed plugin folder was found — the previous run was cut short. Install from scratch?" "Cancel" "Install")
  fi
  case "$answer" in ""|Cancel) exit 0 ;; esac
}   # the folder is removed only once the rest of the answers are in, at the copy

resolve_layout() {  # the chosen folder: earlier versions kept everything under Claude/
  [ -d "$1/Claude/Memory" ] || return 0
  if [ -d "$1/MORF" ]; then
    say "Both layouts are here: memory in Claude/ and a MORF/ folder beside it.\n\nNothing was moved — sort the two out by hand, then run this again."
    return 0
  fi

  local answer
  answer=$(pick "Memory from an earlier version was found in Claude/.\n\nMove Memory, Facts and Docs into MORF/? Records are carried across untouched, and anything else in Claude/ stays where it is." "Leave it" "Move")
  if [ "$answer" = "Move" ]; then
    mkdir -p "$1/MORF"
    for folder in Memory Facts Docs; do
      [ -d "$1/Claude/$folder" ] || continue
      mv "$1/Claude/$folder" "$1/MORF/$folder" \
        || fail "Could not move $folder. Nothing was deleted: move what already landed in MORF/ back, or finish by hand."
    done
    rmdir "$1/Claude" 2>/dev/null || true   # anything of yours still in there stays
  else
    say "Memory stays in Claude/.\n\nMORF/ will be created empty, and the plugin will not see the earlier records until you move those three folders across yourself."
  fi
}

resolve_pointer() {  # the chosen folder -> the folder to actually put MORF in
  # The answer is printed, so nothing else here may reach stdout: `say` sends
  # osascript to /dev/null and `pick` is captured, which is what keeps it clean.
  local old=""
  if [ -f "$POINTER" ]; then
    old=$(cat "$POINTER")
  elif [ -f "$OLD_POINTER" ]; then
    old="$(cat "$OLD_POINTER")/MORF"   # before 1.3 the pointer named the folder above
  fi
  if [ -z "$old" ] || [ "$old" = "$1/MORF" ] || [ ! -d "$old" ]; then
    printf '%s' "$1"
    return 0
  fi

  local answer
  answer=$(pick "MORF is already set up elsewhere:\n$(esc "$old")\n\nSet it up at the selected place instead?\n$(esc "$1")/MORF" "Keep previous" "Set up here")
  if [ "$answer" = "Set up here" ]; then   # dismissing keeps the records reachable
    say "The earlier records stay at\n$(esc "$old")\n\nNothing is moved and nothing is deleted, but the plugin stops looking there. Move them across yourself if you want them."
    printf '%s' "$1"
  else
    printf '%s' "$(dirname "$old")"    # keeping the pointer means installing there again
  fi
}

# ===== Where to install =====

resolve_marketplace
resolve_previous

PLACE=$(osascript -e 'try
  POSIX path of (choose folder with prompt "Choose where to keep the memory. A MORF folder will be created inside.")
on error
  return ""
end try')

[ -z "$PLACE" ] && exit 0
PLACE="${PLACE%/}"

PLACE=$(resolve_pointer "$PLACE")
resolve_layout "$PLACE"

PROJECT=$(osascript -e 'try
  text returned of (display dialog "Name of the first project" default answer "project" with title "MORF")
on error
  return ""
end try')
PROJECT="${PROJECT//\//-}"                              # it becomes a folder name, so
case "$PROJECT" in ""|.*) PROJECT="project" ;; esac     # no separators, no climbing out

# One list, code first: the names are what the picker shows, the codes are how
# the system's own locale is matched, so the list opens on the language in use.
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

SYSTEM_CODE=$(osascript -e 'user locale of (get system info)' 2>/dev/null | cut -d_ -f1 || true)
DEFAULT=$(printf '%s\n' "$LANGUAGES" | grep "^$SYSTEM_CODE:" | cut -d: -f2 || true)
[ -z "$DEFAULT" ] && DEFAULT="English"
NAMES=$(printf '%s\n' "$LANGUAGES" | cut -d: -f2 | sed 's/.*/"&"/' | paste -sd, -)

LANGUAGE=$(osascript -e "try
  set picked to choose from list {$NAMES} with title \"MORF\" with prompt \"Language for observations and fact articles.\n\nImperatives — instructions, commands, rules — stay in English regardless: they load next to Claude Code's own.\" default items {\"$DEFAULT\"}
  if picked is false then return \"\"
  item 1 of picked
on error
  return \"\"
end try")
[ -z "$LANGUAGE" ] && LANGUAGE="$DEFAULT"

# ===== Unpacking =====

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

sed -n '/^__PAYLOAD__$/,$p' "$0" | tail -n +2 | base64 --decode | tar -xzf - -C "$TMP" \
  || fail "Could not unpack the installer payload."

# ===== Plugin =====

rm -rf "$SKILLS_DIR"
mkdir -p "$SKILLS_DIR"
cp -R "$TMP"/. "$SKILLS_DIR"/
rm -rf "$SKILLS_DIR/docs" "$SKILLS_DIR/assets"

# ===== The MORF folder =====

MEMORY="$PLACE/MORF/Memory"
mkdir -p "$MEMORY/Scripts" "$MEMORY/Transcripts" "$MEMORY/$PROJECT" "$PLACE/MORF/Facts" "$PLACE/MORF/Docs" "$PLACE/MORF/Rules"

CHANGED=0
place() {  # source, target: our files are updated, edited ones are kept alongside
  local src="$1" dst="$2"
  if [ -f "$dst" ] && ! cmp -s "$src" "$dst"; then
    cp "$dst" "$dst.$STAMP.bak"
    CHANGED=$((CHANGED + 1))
  fi
  cp "$src" "$dst"
}

for f in "$TMP"/scripts/*.py "$TMP"/scripts/config.json; do
  place "$f" "$MEMORY/Scripts/$(basename "$f")"
done
for f in "$TMP"/assets/*.canvas; do
  place "$f" "$MEMORY/$(basename "$f")"
done
for f in "$TMP"/docs/*.md; do
  place "$f" "$PLACE/MORF/Docs/$(basename "$f")"
done
mkdir -p "$PLACE/MORF/Docs/ru"
for f in "$TMP"/docs/ru/*.md; do
  place "$f" "$PLACE/MORF/Docs/ru/$(basename "$f")"
done

# memory records are never touched: only what is missing gets created
[ -f "$MEMORY/sessions.md" ] || printf '| id | date | project | about |\n|---|---|---|---|\n' > "$MEMORY/sessions.md"
[ -f "$MEMORY/audit.md" ] || printf 'last: none\n\n' > "$MEMORY/audit.md"

for level in L0 L1 L2 L3 dropped; do
  target="$MEMORY/$PROJECT/$level.md"
  [ -f "$target" ] || printf -- '---\nname: %s-%s\n---\n\n' "$PROJECT" "$level" > "$target"
done

printf '%s' "$PLACE/MORF" > "$POINTER"   # the folder itself, not what surrounds it
rm -f "$OLD_POINTER"

# ===== Language =====
# The choice is an instruction to the agent, so it goes where instructions
# load by themselves: the CLAUDE.md of the folder MORF sits in. Markers let a repeat install
# replace only this section and leave the rest of the file alone.

CLAUDE_MD="$PLACE/CLAUDE.md"
BLOCK=$(printf '<!-- morf:language -->\n## Language\n\nImperatives in English: instructions, commands, rules, agent definitions.\nEverything in the indicative — observations, fact articles and replies to me\n— in %s.\n<!-- /morf:language -->' "$LANGUAGE")

if [ -f "$CLAUDE_MD" ] && grep -q '<!-- morf:language -->' "$CLAUDE_MD"; then
  python3 - "$CLAUDE_MD" "$BLOCK" <<'PYEOF'
import re, sys
path, block = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
# callable replacement: not escape-interpreted, unlike a replacement string
text = re.sub(r"<!-- morf:language -->.*?<!-- /morf:language -->", lambda _: block, text, flags=re.S)
open(path, "w", encoding="utf-8").write(text)
PYEOF
elif [ -f "$CLAUDE_MD" ]; then
  printf '\n%s\n' "$BLOCK" >> "$CLAUDE_MD"
else
  printf '# Notes\n\nMemory lives in `MORF/Memory`, fact articles in `MORF/Facts`.\nThe working order is in the `morf` skill.\n\n%s\n' "$BLOCK" > "$CLAUDE_MD"
fi

# ===== Done =====

REPORT="Done.\n\nPlugin: ~/.claude/skills/morf\nMemory: $(esc "$MEMORY")\nFirst project: $(esc "$PROJECT")\nContent language: $(esc "$LANGUAGE")"
[ "$CHANGED" -gt 0 ] && REPORT="$REPORT\n\nEdited files replaced: $CHANGED. Previous versions kept alongside with the .$STAMP.bak suffix"
say "$REPORT\n\nStart Claude Code — the commands appear on their own, type /morf:"

exit 0

__PAYLOAD__
