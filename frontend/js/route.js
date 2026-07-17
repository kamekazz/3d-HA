// Which page are we on? Flask serves the same index.html for "/" and "/edit";
// the path is the only thing that separates the plain viewer from the editor.
// "/" is what a normal user sees: no topbar, no editing chrome, view mode only.
export const canEdit = location.pathname.replace(/\/+$/, '') === '/edit';
