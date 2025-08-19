from ui.onion_skin import OnionSkinManager


class _DummyMainWindow:
    pass


def test_onion_manager_has_pixmap_and_profiling_attrs():
    mgr = OnionSkinManager(_DummyMainWindow())
    # Attributes present with sane defaults
    assert hasattr(mgr, "pixmap_mode")
    assert hasattr(mgr, "pixmap_scale")
    assert hasattr(mgr, "last_update_ms")
    assert mgr.pixmap_mode is False
    assert 0.0 < mgr.pixmap_scale <= 1.0

    # Profiling helper should work in safe mode without a scene
    t = mgr.measure_update_time(runs=5, safe=True)
    assert isinstance(t, float)
    assert t >= 0.0
    assert mgr.last_update_ms == t
