// The behaviours that separate an installed app from a page in a tab. Pure
// document/window side effects; main.js calls initAppShell() once, before
// anything is built. The CSS half (no text selection, no I-beam, overlay
// scrollbars, chrome that slides rather than pops) lives in style.css under
// "app shell"; the install half (manifest, icons, standalone metas) in
// index.html's <head>.

// what gets a haptic tick on touch — the same set style.css gives the
// tap-highlight/press treatment
const TAPPABLE = 'button, .tswitch, .room-card, .cam-tile, .tile.tappable, ' +
                 '.bb-tile.tappable, .chip, .ed-sec > summary';

const isField = (el) => el instanceof Element &&
  !!el.closest('input, textarea, select, [contenteditable]');

export function initAppShell() {
  // No browser context menu over the chrome or the 3D view (a long-press on
  // iPad, right-click on desktop). Fields keep theirs: that is where paste
  // lives. Nothing in the app uses the right button (planner pans on middle).
  document.addEventListener('contextmenu', (e) => {
    if (!isField(e.target)) e.preventDefault();
  });

  // Images don't lift off as drag ghosts (room-card thumbnails, camera
  // snapshots). CSS -webkit-user-drag covers WebKit; this covers the rest.
  document.addEventListener('dragstart', (e) => {
    if (e.target instanceof HTMLImageElement) e.preventDefault();
  });

  // A haptic tick under every tap. Android only — iOS has no web vibration
  // API — and only for a real finger, never a mouse.
  document.addEventListener('pointerdown', (e) => {
    if (e.pointerType !== 'touch' || !navigator.vibrate) return;
    if (e.target instanceof Element && e.target.closest(TAPPABLE)) {
      try { navigator.vibrate(8); } catch { /* not allowed here */ }
    }
  }, { passive: true });

  initWakeLock();
}

// Screen wake lock. This is a wall/hand tablet dashboard: the screen must not
// dim to the lock screen while someone is glancing at it. Held in view mode
// only — edit mode is a workbench, and a laptop left on /edit should sleep
// like any other app. The lock is released by the OS whenever the tab is
// hidden, so it is re-requested on every return to visibility. Unsupported or
// refused (battery saver, some kiosks) is silent: nothing else depends on it.
function initWakeLock() {
  if (!('wakeLock' in navigator)) return;
  let lock = null;
  let wanted = true;   // appMode starts as 'view' (ui.js)

  const acquire = async () => {
    if (!wanted || lock || document.visibilityState !== 'visible') return;
    try {
      lock = await navigator.wakeLock.request('screen');
      lock.addEventListener('release', () => { lock = null; });
    } catch { /* denied — try again on the next visibility change */ }
  };
  const drop = () => { lock?.release(); lock = null; };

  window.addEventListener('appModeChanged', (e) => {
    wanted = e.detail.mode === 'view';
    if (wanted) acquire(); else drop();
  });
  document.addEventListener('visibilitychange', acquire);
  acquire();
}
