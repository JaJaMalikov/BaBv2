from __future__ import annotations

from dataclasses import dataclass

from controllers.settings_service import SettingsSchema
from controllers.settings_presenter import (
    OnionValues,
    schema_to_dialog_onion,
    dialog_onion_to_schema,
    qsettings_to_dialog_onion,
    dialog_onion_to_qsettings,
)


class SpinStub:
    def __init__(self, v: float = 0.0) -> None:
        self._v = float(v)

    def setValue(self, v: int | float) -> None:  # noqa: N802 (Qt naming)
        self._v = float(v)

    def value(self) -> float:  # noqa: N802 (Qt naming)
        return self._v


class DialogStub:
    def __init__(self) -> None:
        self.prev_count = SpinStub()
        self.next_count = SpinStub()
        self.opacity_prev = SpinStub()
        self.opacity_next = SpinStub()


class QSettingsStub:
    def __init__(self) -> None:
        self._data: dict[str, object] = {}

    def value(self, key: str, default: object | None = None) -> object | None:  # noqa: A003
        return self._data.get(key, default)

    def setValue(self, key: str, value: object) -> None:  # noqa: N802 (Qt naming)
        self._data[key] = value


def test_schema_dialog_round_trip_identity_for_symmetric_values():
    schema = SettingsSchema()
    schema.onion_span = 3
    schema.onion_opacity = 0.6

    dlg = DialogStub()
    schema_to_dialog_onion(dlg, schema)

    # Back to schema from dialog
    s2 = dialog_onion_to_schema(dlg)

    assert s2.onion_span == 3
    assert abs(s2.onion_opacity - 0.6) < 1e-9


def test_dialog_to_schema_reduces_as_expected():
    dlg = DialogStub()
    # Asymmetric values in UI should reduce to max span and average opacity
    dlg.prev_count.setValue(2)
    dlg.next_count.setValue(5)
    dlg.opacity_prev.setValue(0.2)
    dlg.opacity_next.setValue(0.6)

    s = dialog_onion_to_schema(dlg)
    assert s.onion_span == 5
    assert abs(s.onion_opacity - 0.4) < 1e-9


def test_qsettings_round_trip_compatibility():
    dlg = DialogStub()
    qs = QSettingsStub()

    # Write values from dialog to qsettings
    dlg.prev_count.setValue(4)
    dlg.next_count.setValue(4)
    dlg.opacity_prev.setValue(0.3)
    dlg.opacity_next.setValue(0.3)
    dialog_onion_to_qsettings(dlg, qs)

    # Now load them back into a fresh dialog using qsettings_to_dialog_onion
    dlg2 = DialogStub()
    qsettings_to_dialog_onion(dlg2, qs)

    assert int(dlg2.prev_count.value()) == 4
    assert int(dlg2.next_count.value()) == 4
    assert abs(dlg2.opacity_prev.value() - 0.3) < 1e-9
    assert abs(dlg2.opacity_next.value() - 0.3) < 1e-9
