"""Module for synchronizing selection and simple UI model change notifications.

DEPRECATION NOTICE (docs/tasks.md §23):
- Direct traversal of `win.object_manager.graphics_items` couples UI to internals.
  This will migrate to a selection service/facade emitting events and providing
  query APIs. Keep calls here stable until the facade is introduced.

Temporary event emission (docs/tasks.md §7):
- Provide a minimal, loosely-coupled hook to notify UI widgets that the
  underlying model has changed so they can refresh themselves without direct
  cross-calls between unrelated UI modules.
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Set
from weakref import WeakKeyDictionary
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Qt

# Re-entrancy guard to avoid selection feedback loops between facade and scene
_in_facade_selection: bool = False

# Subscribers are registered per-main-window to avoid global coupling.
# WeakKeyDictionary ensures windows can be GC'ed without manual cleanup.
_model_changed_subs: "WeakKeyDictionary[Any, Set[Callable[[], None]]]" = WeakKeyDictionary()


def subscribe_model_changed(win: Any, callback: Callable[[], None]) -> None:
    """Subscribe a callback to be invoked when the model changes for this window.

    - Stores callbacks in a weak-keyed registry keyed by the window instance.
    - The callback signature is () -> None.
    """
    subs = _model_changed_subs.get(win)
    if subs is None:
        subs = set()
        _model_changed_subs[win] = subs
    subs.add(callback)


def unsubscribe_model_changed(win: Any, callback: Callable[[], None]) -> None:
    """Unsubscribe a previously registered callback for this window."""
    subs = _model_changed_subs.get(win)
    if not subs:
        return
    subs.discard(callback)
    # Clean up empty sets to keep registry tidy
    if not subs:
        try:
            del _model_changed_subs[win]
        except Exception:
            pass


# --- Simple model-changed emission -------------------------------------------------

def emit_model_changed(win: Any) -> None:
    """Emit a lightweight 'model changed' notification to interested UI parts.

    Order of notifications (backward compatible):
    1) Notify explicit subscribers registered via subscribe_model_changed.
    2) If the main window exposes `on_model_changed`, call it.
    3) Fallback: refresh the inspector widget if present.
    """
    # 1) Notify subscribers
    subs = list(_model_changed_subs.get(win, set()))
    for cb in subs:
        try:
            cb()
        except Exception:
            # Best-effort: never let a subscriber break the chain
            pass

    # 2) Optional handler on the window
    handler: Optional[Callable[[], None]] = getattr(win, "on_model_changed", None)
    if callable(handler):
        try:
            handler()
        except Exception:
            pass
        # Continue to fallback to preserve previous behavior if needed

    # 3) Fallback to current InspectorWidget refresh behavior to keep UI in sync
    insp = getattr(win, "inspector_widget", None)
    if insp and hasattr(insp, "refresh"):
        try:
            insp.refresh()
        except Exception:
            pass


# --- Selection synchronization -----------------------------------------------------

def select_object_in_inspector(win: Any, name: str) -> None:
    """Select the given object name in the inspector list, if present and visible.

    Keeps previous behavior: selects only 'object' entries matching name.
    """
    insp = getattr(win, "inspector_widget", None)
    if not insp:
        return
    lw: QListWidget = insp.list_widget
    for i in range(lw.count()):
        it: QListWidgetItem = lw.item(i)
        typ, nm = it.data(Qt.UserRole)
        if typ == "object" and nm == name:
            lw.setCurrentItem(it)
            break


def scene_selection_changed(win: Any) -> None:
    """When the scene selection changes, highlight the corresponding item in the inspector."""
    try:
        selected = win.scene.selectedItems()
    except RuntimeError:
        # Scene already deleted; ignore stale signal during teardown
        return
    if not selected:
        return
    item = selected[0]
    for name, gi in win.object_manager.graphics_items.items():
        if gi is item and name in win.scene_model.objects:
            select_object_in_inspector(win, name)
            # Bridge to facade selection model if present, unless we're already
            # handling a facade-driven selection to avoid feedback loops.
            fac = getattr(win, "scene_facade", None)
            if fac and not _in_facade_selection:
                try:
                    fac.select_object(name)
                except Exception:
                    pass
            return



def highlight_scene_object(win: Any, name: str) -> None:
    """Highlight the given scene object by name in the QGraphicsScene.

    Centralizes selection operations instead of calling setSelected directly
    from various UI components (docs/tasks.md §3, §16).
    """
    try:
        # Clear current selection
        for it in win.scene.selectedItems():
            it.setSelected(False)
    except Exception:
        # If scene not initialized, ignore gracefully
        return
    gi = getattr(win.object_manager, "graphics_items", {}).get(name)
    if gi is not None and getattr(gi, "isVisible", lambda: True)():
        try:
            gi.setSelected(True)
        except Exception:
            pass


def bind_facade_selection(win: Any) -> None:
    """Bind SceneFacade selection events to UI highlights and inspector selection.

    - Subscribes to selection changes from the facade (if available).
    - Highlights graphics items and selects the corresponding row in the inspector.
    """
    fac = getattr(win, "scene_facade", None)
    if not fac or not hasattr(fac, "add_selection_listener"):
        return

    def _on_sel(kind: str | None, name: str | None) -> None:
        global _in_facade_selection
        _in_facade_selection = True
        try:
            if not name:
                # Clear scene selection
                try:
                    for it in win.scene.selectedItems():
                        it.setSelected(False)
                except Exception:
                    pass
                return
            if kind == "object":
                highlight_scene_object(win, name)
                select_object_in_inspector(win, name)
            elif kind == "puppet":
                # For now, only sync inspector selection for puppets
                insp = getattr(win, "inspector_widget", None)
                if insp:
                    lw: QListWidget = insp.list_widget
                    for i in range(lw.count()):
                        it: QListWidgetItem = lw.item(i)
                        typ, nm = it.data(Qt.UserRole)
                        if typ == "puppet" and nm == name:
                            lw.setCurrentItem(it)
                            break
        finally:
            _in_facade_selection = False

    try:
        fac.add_selection_listener(_on_sel)
    except Exception:
        pass
