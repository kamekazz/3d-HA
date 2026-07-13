"""Session-only undo/redo history for the house layout.

Holds full JSON snapshots of the layout tables (a few KB each — see
HouseStore.export_snapshot). Lives in memory only: restarting the app clears
the history, which is the agreed behavior. History and the store each have
their own lock; the snapshot-then-mutate pair in routes.py is not atomic
across threads, but this is a single-user app on sync Flask.
"""
import json
import threading

CAP = 100  # max undo steps kept; snapshots are small, 100 is plenty


def _dumps(snap):
    return json.dumps(snap, sort_keys=True, separators=(",", ":"))


class HouseHistory:
    def __init__(self):
        self._lock = threading.Lock()
        self._undo = []  # JSON strings: state BEFORE each recorded mutation
        self._redo = []  # JSON strings: states stepped back from

    def record(self, before_snap):
        """Called after a successful mutation with the pre-mutation snapshot."""
        with self._lock:
            self._undo.append(_dumps(before_snap))
            del self._undo[:-CAP]
            self._redo.clear()  # a new edit invalidates the redo branch

    def undo(self, current_snap):
        """Pop the state to restore; push current onto redo. None if empty."""
        with self._lock:
            if not self._undo:
                return None
            self._redo.append(_dumps(current_snap))
            return json.loads(self._undo.pop())

    def redo(self, current_snap):
        with self._lock:
            if not self._redo:
                return None
            self._undo.append(_dumps(current_snap))
            return json.loads(self._redo.pop())

    def restore_failed(self, snap, was_undo):
        """restore_snapshot raised: put the stacks back the way they were."""
        with self._lock:
            if was_undo:
                self._undo.append(_dumps(snap))
                self._redo.pop()
            else:
                self._redo.append(_dumps(snap))
                self._undo.pop()

    def counts(self):
        with self._lock:
            return {"can_undo": bool(self._undo), "can_redo": bool(self._redo)}
