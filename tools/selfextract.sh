#!/bin/sh
# MORF — self-extracting installer.
#
# One file: this header, then a base64 tar of the payload (install.sh plus the
# scripts, hooks, commands, docs and canvas that make up a `.morf/`) appended
# after the `__PAYLOAD__` line. It unpacks to a temp dir and runs install.sh
# from there, so a `.morf` can be dropped into a repo without cloning MORF.
#
#   sh install-morf.sh                 install into the git top-level of the cwd
#   sh install-morf.sh <target-repo>   install into that repository
#   sh install-morf.sh --lang German   set the content language
#   sh install-morf.sh --private       keep the whole .morf (skip data .gitignore)
#
# All arguments are passed straight through to install.sh.

set -eu

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Everything after the marker line is the base64 payload.
sed -n '/^__PAYLOAD__$/,$p' "$0" | tail -n +2 | base64 --decode | tar -xzf - -C "$TMP" || {
  echo "install-morf: could not unpack the payload." >&2
  exit 1
}

[ -f "$TMP/install.sh" ] || { echo "install-morf: payload has no install.sh." >&2; exit 1; }
exec sh "$TMP/install.sh" "$@"

__PAYLOAD__
