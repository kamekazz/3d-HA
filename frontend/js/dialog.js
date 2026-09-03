// In-app alert and confirm sheets. window.alert/confirm are the browser's
// own dialogs: OS-styled, titled with the origin ("127.0.0.1:5000 says") and
// the single loudest tell that this is a web page and not an app. This is one
// <dialog> in the top layer — above the planner (z 60) and the model library
// (z 70) with no z-index bookkeeping — styled as an Apple alert, and awaited
// where the natives were called: `await showConfirm(...)` stands where
// `confirm(...)` stood. Esc, the backdrop and Cancel all resolve false.
// Requests queue, so a loop that raises three failures shows them in turn
// instead of stacking.

let dlg = null;
let settle = null;         // resolver of the sheet currently up
let queue = Promise.resolve();

function build() {
  dlg = document.createElement('dialog');
  dlg.id = 'app-dialog';
  dlg.innerHTML = `
    <h2 id="ad-title"></h2>
    <p id="ad-msg"></p>
    <div class="ad-actions">
      <button type="button" id="ad-cancel" class="secondary">Cancel</button>
      <button type="button" id="ad-ok">OK</button>
    </div>`;
  document.body.appendChild(dlg);
  dlg.querySelector('#ad-cancel').onclick = () => finish(false);
  dlg.querySelector('#ad-ok').onclick = () => finish(true);
  // Esc fires `cancel`; route it through finish so every exit lands in one place
  dlg.addEventListener('cancel', (e) => { e.preventDefault(); finish(false); });
  // a tap on the backdrop targets the dialog itself — tell it apart from a
  // tap on the sheet's own padding by the box
  dlg.addEventListener('click', (e) => {
    if (e.target !== dlg) return;
    const r = dlg.getBoundingClientRect();
    const inside = e.clientX >= r.left && e.clientX <= r.right &&
                   e.clientY >= r.top && e.clientY <= r.bottom;
    if (!inside) finish(false);
  });
}

function finish(value) {
  if (!settle) return;
  const done = settle;
  settle = null;
  dlg.close();
  done(value);
}

function present({ title, message, okLabel, cancelLabel, danger, confirm }) {
  if (!dlg) build();
  return new Promise((resolve) => {
    settle = resolve;
    dlg.querySelector('#ad-title').textContent = title || '';
    dlg.querySelector('#ad-msg').textContent = message || '';
    const ok = dlg.querySelector('#ad-ok');
    const cancel = dlg.querySelector('#ad-cancel');
    ok.textContent = okLabel;
    ok.classList.toggle('danger', !!danger);
    cancel.textContent = cancelLabel;
    cancel.classList.toggle('hidden', !confirm);
    dlg.showModal();
    // a destructive confirm defaults to the safe button, like a native alert
    (danger ? cancel : ok).focus();
  });
}

function enqueue(opts) {
  const p = queue.then(() => present(opts));
  queue = p.catch(() => {});
  return p;
}

/** Message with one OK button. Resolves when dismissed. */
export function showAlert(message, { title = '', okLabel = 'OK' } = {}) {
  return enqueue({ title, message, okLabel, confirm: false });
}

/** OK/Cancel. Resolves true only on OK; `danger` styles OK as destructive. */
export function showConfirm(message, { title = '', okLabel = 'OK', cancelLabel = 'Cancel',
                                       danger = false } = {}) {
  return enqueue({ title, message, okLabel, cancelLabel, danger, confirm: true });
}
