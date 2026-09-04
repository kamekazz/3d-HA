#!/bin/sh
# usage: sh r2_shoot.sh <tag> <room:level> ...
cd "$(dirname "$0")" || exit 1
TAG="$1"; shift
PY=../backend/.venv/Scripts/python.exe
for spec in "$@"; do
  room="${spec%%:*}"; lvl="${spec##*:}"
  out="../scratchpad/lightgauntlet/shots/r${room}_${TAG}"
  echo "=== room $room level $lvl -> $out"
  "$PY" -m roomkit.lightshot --room "$room" --level "$lvl" --out "$out" \
      > "../scratchpad/lightgauntlet/shots/r${room}_${TAG}.json" 2>&1
  tail -c 400 "../scratchpad/lightgauntlet/shots/r${room}_${TAG}.json"
  echo
done
echo "ALL DONE"
