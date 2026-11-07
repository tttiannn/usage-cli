#!/bin/sh
set -eu

force=false
case "${1-}" in
  '') ;;
  --force) force=true ;;
  *) printf '%s\n' 'Usage: sh install.sh [--force]' >&2; exit 2 ;;
esac
if [ "$#" -gt 1 ]; then
  printf '%s\n' 'Usage: sh install.sh [--force]' >&2
  exit 2
fi
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
destination="$HOME/.local/bin/usage"
if [ -e "$destination" ] || [ -L "$destination" ]; then
  if [ "$force" != true ] && ! cmp -s "$project_dir/bin/usage" "$destination"; then
    printf '%s\n' "Refusing to overwrite $destination. Review it, then use --force to replace it." >&2
    exit 1
  fi
fi
mkdir -p "$HOME/.local/bin"
# Remove a symlink rather than writing through it to another file.
if [ -L "$destination" ]; then
  rm "$destination"
fi
install -m 755 "$project_dir/bin/usage" "$destination"
printf '%s\n' "Installed $destination"
printf '%s\n' 'Ensure ~/.local/bin is on PATH. Run usage --help to get started.'
