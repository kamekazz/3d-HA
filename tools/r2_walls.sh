#!/bin/sh
# usage: sh r2_walls.sh <tag> [roomlist...]   default: all six
cd "$(dirname "$0")" || exit 1
TAG="$1"; shift
PY=../backend/.venv/Scripts/python.exe
S=../scratchpad/lightgauntlet/shots
run() { # room level pos target
  echo "=== room $1 -> $S/w$1_$TAG"
  "$PY" r2_wall.py --room "$1" --level "$2" --pos "$3" --target "$4" \
     --fov 55 --band 0.33,0.44 --out "$S/w$1_$TAG" 2>&1 | grep -v Warning \
     > "$S/w$1_$TAG.json"
  "$PY" -c "
import json,sys
t=open('$S/w$1_$TAG.json').read(); d=json.loads(t[t.index('{'):])
print('  ON  band',d['on']['band'],'meter',d['on']['meter'])
print('  OFF band',d['off']['band'],'meter',d['off']['meter'],'delta',d['delta'])
print('  slots',d['on']['slots'])
"
}
want() { case " $* " in *" $1 "*) return 0;; esac; [ -z "$*" ] && return 0; return 1; }

for r in "$@"; do
  case "$r" in
    1) run 1 0 8.3,4.2,22    8.3,4.2,34.9 ;;
    2) run 2 0 8.25,4.2,-1.0 8.25,4.2,11.4 ;;
    5) run 5 1 8.35,12.0,-8.0 8.35,12.0,4.6 ;;
    6) run 6 1 3.25,12.0,10.5 3.25,12.0,21.4 ;;
    7) run 7 1 29.1,12.0,22.5 29.1,12.0,34.7 ;;
    8) run 8 1 30.5,12.0,1.3  39.4,12.0,1.3 ;;
  esac
done
echo "WALLS DONE"
