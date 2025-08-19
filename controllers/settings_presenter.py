from __future__ import annotations

"""Settings dialog presenter/adapter.

Purpose:
- Bridge between the pure SettingsService schema and the Qt SettingsDialog widgets
  without coupling persistence rules to the UI layer.
- Provide small helpers to read/write onion-skin related controls and to map
  them to the portable SettingsSchema fields.

This addresses docs/tasks.md 7.2 (extract presenter/adapter) while keeping
existing SettingsManager behavior intact. Future extensions can add bindings for
additional tabs/controls.
"""

from dataclasses import dataclass
from typing import Protocol

from controllers.settings_service import SettingsSchema


class _SpinLike(Protocol):
    def setValue(self, v: int | float) -> None: ...
    def value(self) -> int | float: ...


class OnionControls(Protocol):
    prev_count: _SpinLike
    next_count: _SpinLike
    opacity_prev: _SpinLike
    opacity_next: _SpinLike


@dataclass
class OnionValues:
    prev_count: int = 2
    next_count: int = 1
    opacity_prev: float = 0.25
    opacity_next: float = 0.18

    @staticmethod
    def from_schema(s: SettingsSchema) -> "OnionValues":
        # Map schema (single span/opacity) to symmetric UI controls
        span = max(int(s.onion_span), 0)
        op = float(s.onion_opacity)
        return OnionValues(prev_count=span, next_count=span, opacity_prev=op, opacity_next=op)

    def to_schema(self) -> SettingsSchema:
        # Reduce UI values into a compact schema representation
        # - span: the max of prev/next counts
        # - opacity: average of prev/next (simple, deterministic)
        span = max(int(self.prev_count), int(self.next_count))
        op = (float(self.opacity_prev) + float(self.opacity_next)) / 2.0
        sch = SettingsSchema()
        sch.onion_span = span
        sch.onion_opacity = op
        return sch


def apply_onion_to_dialog(dlg: OnionControls, values: OnionValues) -> None:
    """Populate dialog controls from onion values."""
    dlg.prev_count.setValue(int(values.prev_count))
    dlg.next_count.setValue(int(values.next_count))
    dlg.opacity_prev.setValue(float(values.opacity_prev))
    dlg.opacity_next.setValue(float(values.opacity_next))


def extract_onion_from_dialog(dlg: OnionControls) -> OnionValues:
    """Extract onion values from dialog controls."""
    return OnionValues(
        prev_count=int(dlg.prev_count.value()),
        next_count=int(dlg.next_count.value()),
        opacity_prev=float(dlg.opacity_prev.value()),
        opacity_next=float(dlg.opacity_next.value()),
    )


def schema_to_dialog_onion(dlg: OnionControls, schema: SettingsSchema) -> None:
    """Apply schema onion config into dialog controls."""
    apply_onion_to_dialog(dlg, OnionValues.from_schema(schema))


def dialog_onion_to_schema(dlg: OnionControls) -> SettingsSchema:
    """Build a schema containing only onion fields from dialog controls."""
    return extract_onion_from_dialog(dlg).to_schema()


def qsettings_to_dialog_onion(dlg: OnionControls, qsettings) -> None:  # type: ignore[no-untyped-def]
    """Backwards-compatible loader from QSettings into dialog onion controls.

    Keeps existing key names used by SettingsManager to avoid breaking runtime behavior.
    """
    try:
        prev_count = int(qsettings.value("onion/prev_count", 2))
        next_count = int(qsettings.value("onion/next_count", 1))
        op_prev = float(qsettings.value("onion/opacity_prev", 0.25))
        op_next = float(qsettings.value("onion/opacity_next", 0.18))
    except Exception:
        prev_count, next_count, op_prev, op_next = 2, 1, 0.25, 0.18
    apply_onion_to_dialog(
        dlg,
        OnionValues(
            prev_count=prev_count,
            next_count=next_count,
            opacity_prev=op_prev,
            opacity_next=op_next,
        ),
    )


def dialog_onion_to_qsettings(dlg: OnionControls, qsettings) -> None:  # type: ignore[no-untyped-def]
    """Write dialog onion controls back to QSettings using legacy keys."""
    vals = extract_onion_from_dialog(dlg)
    qsettings.setValue("onion/prev_count", int(vals.prev_count))
    qsettings.setValue("onion/next_count", int(vals.next_count))
    qsettings.setValue("onion/opacity_prev", float(vals.opacity_prev))
    qsettings.setValue("onion/opacity_next", float(vals.opacity_next))


__all__ = [
    "OnionControls",
    "OnionValues",
    "apply_onion_to_dialog",
    "extract_onion_from_dialog",
    "schema_to_dialog_onion",
    "dialog_onion_to_schema",
    "qsettings_to_dialog_onion",
    "dialog_onion_to_qsettings",
]
