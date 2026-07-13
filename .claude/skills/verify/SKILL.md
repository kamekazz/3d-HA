---
name: verify
description: How to launch and drive this app to verify changes end-to-end (Flask + Three.js frontend, no test suite).
---

# Verifying changes in this repo

No tests/linter/build — verify by running the app and driving it in a browser.

## Launch

Port 5000 is usually taken by the user's own dev server (check
`Get-NetTCPConnection -LocalPort 5000 -State Listen`). Don't kill it — launch a
second instance on 5001 (SQLite handles the shared `backend/house.db` fine):

```powershell
cd backend
.venv\Scripts\python.exe -c "from app import create_app; from realtime.socketio import socketio; app = create_app(); socketio.run(app, host='127.0.0.1', port=5001, debug=False, allow_unsafe_werkzeug=True)"
```

Run in background; wait for `http://127.0.0.1:5001/api/house/history` (or any
GET endpoint) to respond. Stop it when done (find pid via the port).

## Gotchas

- `backend/house.db` is TRACKED in git (demo data). Layout edits made during
  verification mutate it. Either end the session with all edits undone
  (undo/redo feature), or restore. Even a logically-identical DB shows as
  `M` in git status (SQLite page churn) — compare table contents, not bytes:
  extract HEAD's copy with **Git Bash** (`git show HEAD:backend/house.db >
  file` — PowerShell `>` corrupts binary) and diff `SELECT * FROM <table>
  ORDER BY id` per table.
- Backend logic can be smoke-tested headlessly with Flask's test client +
  a temp DB: build a minimal Flask app, register `house.routes.bp`, set
  `app.extensions` `house_store`/`house_history` and a stub `ha_cache`
  (needs `.ready = False` and `ha_floors()`); don't use `create_app()` in
  tests — it starts the HA websocket thread against the real instance.
- Browser (claude-in-chrome): screenshot coords ≠ CSS pixels — the window is
  ~2518 CSS px wide but screenshots are ~1514-1568. Scale click targets by
  (screenshot width / window.innerWidth). Get element centers via
  `getBoundingClientRect()` in javascript_tool, then scale.
- Native color inputs open an OS picker that blocks automation — set
  `.value` and `dispatchEvent(new Event('change'))` instead; that drives the
  same `onchange` commit path.
- Planner overlay: rooms are clickable on the canvas; gestures commit on
  pointerup (one PATCH each). The props panel is on the right.
- Console tracking in claude-in-chrome starts on first read — call
  read_console_messages early or reload the page before checking for errors.
