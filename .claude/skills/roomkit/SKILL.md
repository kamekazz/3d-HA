---
name: roomkit
description: "How the house gets furnished — the roomkit toolchain (glb.py / place.py / rooms.py / dollhouse.py / meter.py), the build -> shoot -> blind-critic loop, and the per-room size budgets. Use for any room-building, furnishing, or render-vs-photo work under tools/roomkit/ or scratchpad/<room>/."
---

# The room build ("roomkit") — how the house gets furnished

Every room is being rebuilt as procedural geometry until a critic can't tell the render from the
photograph of the real room. **Start any room work by reading `tools/roomkit/RESUME.md`** — it
carries the current state, the open critic verdicts and what to do next; then `ROOM-BRIEF.md`
(toolchain + every lesson the critic reports have produced) and `STYLE-BAR.md` (the Sims 4
dollhouse bar). Per-room piece maps live in `tools/roomkit/rooms/<id>.json`; whole-house state in
`house_status.json`, rendered to a shareable page by `python -m roomkit.house_progress` (run from
`tools/`).

`tools/roomkit/` is the toolchain: `glb.py` writes GLBs by hand (no Blender), `place.py` uploads
and positions them through the normal `/api/house/model` + `/api/house/room/<id>/object` endpoints,
`rooms.py` shoots a room from the reference photo's viewpoint or from a `doll_se/sw/ne/nw`
cutaway quadrant, `dollhouse.py` shoots the whole house with every floor visible, `meter.py`
compares render against photo. Per-room build scripts live in `scratchpad/<room>/` (e.g.
`scratchpad/lr5/`, `scratchpad/kbuild/`) and are idempotent and re-runnable, keyed by piece name.

The loop is build → shoot → **blind** critic verdict → next round. Two rules that have each cost a
round: `roomkit.meter` only measures an *empty* room (its centre patch lands on furniture
otherwise — meter furnished rooms by hand), and standard deviation is scale-blind, so match
mean|Δ| between adjacent pixels too, at native resolution. Budgets: **≤1.5 MB per room, ≤300 KB
per piece** — take fine gradients from a tiled texture, not from mesh cells.
