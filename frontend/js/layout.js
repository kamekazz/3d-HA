// Reads back what the CSS layout tokens actually resolved to.
//
// getPropertyValue on an UNREGISTERED custom property returns the token
// stream, not a used value — '--stage-left' comes back as the literal string
// "calc(env(safe-area-inset-left,0px) + 20px)", which no parseFloat can
// rescue. So resolve through the layout engine instead: assign the token to a
// probe's width and read the box back. (@property with syntax:'<length>' would
// make getPropertyValue work directly, but it needs iPadOS 16.4+; the probe
// needs nothing.)
//
// Prefer the USED value over the token wherever one exists —
// parseFloat(getComputedStyle(el).columnGap) cannot drift at all. This module
// is for the tokens that have no element to read them off.

let probe = null;
const cache = new Map();

function ensureProbe() {
  if (probe) return probe;
  probe = document.createElement('div');
  probe.setAttribute('aria-hidden', 'true');
  probe.style.cssText =
    'position:fixed;left:-9999px;top:0;height:0;visibility:hidden;pointer-events:none';
  document.body.appendChild(probe);
  return probe;
}

/** A length token, in CSS px. e.g. tokenPx('--head-h') */
export function tokenPx(name) {
  if (cache.has(name)) return cache.get(name);
  const p = ensureProbe();
  p.style.width = `var(${name})`;
  const v = p.getBoundingClientRect().width;
  cache.set(name, v);
  return v;
}

/** A unitless token. e.g. tokenNum('--card-aspect') */
export function tokenNum(name) {
  return parseFloat(
    getComputedStyle(document.documentElement).getPropertyValue(name));
}

/** Media queries can change a token — the layout bus clears the cache. */
export function invalidateTokens() { cache.clear(); }
