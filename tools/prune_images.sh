#!/usr/bin/env bash
# Prune throwaway render output from scratchpad/ (+ two unreferenced root screenshots).
#
# Everything removed here is build/critic-loop OUTPUT: nothing in the running app,
# no build script, and no kept doc reads any of it. Kept inside scratchpad/:
#   - lightgauntlet/ref/*        external Sims 4 reference shots (an INPUT, not regenerable)
#   - FINAL_* / final_*          the named final shots
#   - anything cited by filename in tools/roomkit/**, frontend/**, CLAUDE.md
#
# Every file is tracked in git, so any of it comes back with:
#   git checkout HEAD -- <path>
#
# Usage:  bash tools/prune_images.sh          # dry run (default)
#         bash tools/prune_images.sh --apply  # actually delete
set -euo pipefail
cd "$(dirname "$0")/.."
LIST="tools/prune_images.list"
EXTRA=(floor2_check.png guest_focus.png)

apply=0
[ "${1:-}" = "--apply" ] && apply=1

n=0; bytes=0
while IFS= read -r f; do
  [ -f "$f" ] || continue
  n=$((n+1)); bytes=$((bytes + $(stat -c%s "$f")))
  [ "$apply" = 1 ] && rm -f -- "$f"
done < "$LIST"

for f in "${EXTRA[@]}"; do
  [ -f "$f" ] || continue
  n=$((n+1)); bytes=$((bytes + $(stat -c%s "$f")))
  [ "$apply" = 1 ] && rm -f -- "$f"
done

if [ "$apply" = 1 ]; then
  find scratchpad -type d -empty -delete 2>/dev/null || true
  printf 'Deleted %d files, %.1f MB.\n' "$n" "$(awk -v b=$bytes 'BEGIN{print b/1048576}')"
  echo 'Recover anything with: git checkout HEAD -- <path>'
else
  printf 'DRY RUN: would delete %d files, %.1f MB.\n' "$n" "$(awk -v b=$bytes 'BEGIN{print b/1048576}')"
  echo 'Re-run with --apply to do it.'
fi
