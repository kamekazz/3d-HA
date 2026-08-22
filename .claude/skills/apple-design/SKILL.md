---
name: apple-design
description: "Apple.com's design language as a full token spec (Action Blue #0066cc, SF Pro ladder, 8px spacing, one drop-shadow, pill CTAs, light/dark full-bleed tile rhythm). Use when designing or restyling UI chrome in this repo — topbar, panels, level selector, planner overlay, buttons, banners, model/plan dialogs — or when asked for an \"Apple-style\" / \"Apple-like\" look anywhere."
---

# Apple design language

Source: [VoltAgent/awesome-design-md · design-md/apple](https://github.com/VoltAgent/awesome-design-md/tree/main/design-md/apple)
(vendored verbatim, version `alpha`).

**The spec is `reference/DESIGN.md` — read it before writing any CSS.** It carries the full
machine-readable token block in its frontmatter (colors, typography, spacing, rounded, shadows,
components) plus prose sections: Overview · Colors · Typography · Layout · Elevation & Depth ·
Shapes · Components · Do's and Don'ts · Responsive Behavior · Iteration Guide · Known Gaps.

## The five rules that carry the look

1. **One accent.** Action Blue `#0066cc` on light, Sky Link Blue `#2997ff` on dark. There is no
   second brand color — every "click me" is that blue.
2. **One shadow.** `rgba(0,0,0,.22) 3px 5px 30px` and only under product imagery resting on a
   surface. Never on cards, buttons, or text. UI elevation comes from surface-color change and
   `backdrop-filter`, not from shadows.
3. **Weight 500 does not exist.** The ladder is 300 / 400 / 600 / 700. Body is 17px / 400 / 1.47
   with `letter-spacing: -0.374px`; display is 600 with negative tracking (−0.28 → −0.374px).
4. **The color change is the divider.** Full-bleed light ↔ near-black tiles stack edge-to-edge with
   no gap, no border, no rounding, no gradient.
5. **Radii don't blend.** 8px compact utility · 18px utility cards · pill (9999px) for primary CTAs
   and chips. Nothing in between. Press state is `transform: scale(0.95)` system-wide.

## Applying it in this repo

`frontend/css/style.css` already defines a **glassy dark** token set at `:root` (`--bg`, `--glass-bg`,
`--accent: #2b6cb0`, `--radius-*`, `--shadow`, `--font: Outfit`) and the whole UI is built on it.
That language and Apple's are not compatible in the details — Apple bans the decorative shadow this
app uses on every `.glass` surface, and its type ramp assumes SF Pro, not Outfit.

So don't half-merge them. Either:

- **Retheme** — rewrite the `:root` block to Apple's tokens and let every existing rule inherit,
  keeping the variable *names* so no selector has to change. This is the cheap, whole-app path.
- **Borrow one axis** — take the type ladder, or the radius scale, or the single-accent rule, and
  apply it consistently everywhere rather than to one panel.

Whichever you pick, say which one you're doing before you start, and never inline a hex — go
through the `:root` variables (the spec's Iteration Guide rule 3, expressed in this repo's terms).

The 3D scene itself (`frontend/js/scene.js`, `daylight.js`, room materials) is lit and colored from
Home Assistant state, not from CSS — this spec governs the 2D chrome only.
