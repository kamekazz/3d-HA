# Active rear capture poses

Use `canonical_poses.json` with `workflow_capture.cjs` for new reviews.
It collects the reviewed poses from the files below without changing source
geometry or the lighting contract. All captures are actual app canvas output.

| View | Authoritative source | Notes |
| --- | --- | --- |
| photo09 | elevation_poses.json | North rear elevation, 66°; approximate full-frame correspondence |
| photo14 | deck_layout_poses.json | Lower deck toward slider/workbench, registered roll included |
| photo02 | deck_layout_poses.json | NE deck toward TV/wing wall |
| photo11 | lake_r2_poses.json | Shore view after 20-foot lawn expansion |
| photo12 | lake_r2_poses.json | Grass beside the expanded lawn's lake border |
| rear_site | site_poses.json | Wide overhead spacing review, no matching ground photograph |
| lawn_spacing | site_poses.json | House-side overhead view across open lawn to the lake; layout review only |

The 105° `photo09-fit-poses.json` experiment was rejected: fitting only the
gable and door exaggerated foreground deck perspective. Do not use it for
review or geometry decisions. Other `*-fit*` and `workflow_matched_poses.json`
files are experiments or superseded positions. In particular, the latter's
photo12 still used the old shoreline location.

Native photo comparisons are at the supplied photograph's pixel dimensions.
Focused component crops use the same crop rectangle after render downsampling.
They are separate diagnostics, never a substitute for the full-frame gate.
