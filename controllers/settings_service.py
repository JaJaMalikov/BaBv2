from __future__ import annotations

"""Qt-agnostic settings service and schema.

Implements docs/plan.md section 4 (SettingsManager refactor) and docs/tasks.md 7.1/7.3:
- Extract a pure SettingsService (no Qt imports) responsible for schema/defaults
  and JSON import/export with basic validation and versioning.
- Define a dataclass-backed SettingsSchema with sane defaults.

This module is intentionally decoupled from UI. A future presenter/adapter can
bind these values to Qt widgets without changing persistence logic.
"""

from dataclasses import dataclass, asdict, fields
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
import json


PROFILE_VERSION = 1
PROFILE_NAMESPACE = "bab"


@dataclass
class SettingsSchema:
    """Stable representation of user settings with defaults.

    Only include keys that are broadly useful and safe to evolve. UI-specific
    concerns (like live widget instances) must not appear here.
    """

    theme: str = "dark"  # theme name identifier
    onion_opacity: float = 0.5  # 0..1
    onion_span: int = 2  # number of frames before/after
    # Onion skin performance options
    onion_pixmap_mode: bool = False  # render onion puppet clones as pixmaps
    onion_pixmap_scale: float = 0.5  # 0<scale<=1, downscale ratio for pixmap rendering
    last_open_dir: Optional[str] = None
    last_save_dir: Optional[str] = None

    # Future examples (add conservatively with defaults):
    # show_handles: bool = True
    # timeline_zoom: float = 1.0


class SettingsService:
    """Pure service to load/save settings profiles.

    The JSON profile structure is:
    {
      "namespace": "bab",
      "version": 1,
      "data": { ... schema fields ... }
    }

    Unknown fields in "data" are ignored. Missing fields fall back to defaults.
    Version mismatches are tolerated with a warning in the returned issues list.
    """

    namespace: str = PROFILE_NAMESPACE
    version: int = PROFILE_VERSION

    @staticmethod
    def key(*parts: str) -> str:
        """Build a namespaced key path for QSettings usage.

        This does not import Qt; UI code can use it to ensure consistent
        namespacing: e.g., SettingsService.key("ui", "theme") -> "bab/ui/theme".
        """
        safe = [SettingsService.namespace]
        safe.extend(str(p).strip("/ ") for p in parts if p)
        return "/".join(safe)

    @staticmethod
    def defaults() -> SettingsSchema:
        """Return a new SettingsSchema with default values."""
        return SettingsSchema()

    @staticmethod
    def to_profile_dict(settings: SettingsSchema) -> Dict[str, Any]:
        """Serialize schema to a namespaced, versioned dict suitable for JSON."""
        return {
            "namespace": SettingsService.namespace,
            "version": SettingsService.version,
            "data": asdict(settings),
        }

    @staticmethod
    def from_profile_dict(profile: Dict[str, Any]) -> Tuple[SettingsSchema, List[str]]:
        """Build schema from a profile dict, returning (schema, issues).

        - Ignores unknown keys in data.
        - Fills missing fields with defaults.
        - Records issues for wrong namespace or version changes.
        """
        issues: List[str] = []
        ns = profile.get("namespace")
        ver = profile.get("version")
        if ns != SettingsService.namespace:
            issues.append(f"unexpected namespace: {ns!r}")
        if not isinstance(ver, int):
            issues.append("missing or invalid version; expected int")
        elif ver != SettingsService.version:
            issues.append(f"profile version {ver} != expected {SettingsService.version}")

        data = profile.get("data")
        if not isinstance(data, dict):
            issues.append("missing or invalid data section")
            data = {}

        # Start from defaults and override known fields.
        result = SettingsService.defaults()
        known = {f.name for f in fields(SettingsSchema)}
        for k, v in data.items():
            if k in known:
                try:
                    setattr(result, k, v)  # type: ignore[attr-defined]
                except Exception as exc:  # defensive; keep robust
                    issues.append(f"failed to apply field {k!r}: {exc}")
            else:
                # ignore unknown fields
                issues.append(f"ignored unknown field {k!r}")
        return result, issues

    # ------------------------------------------------------------------
    # File I/O
    @staticmethod
    def load_json(path: Path) -> Tuple[SettingsSchema, List[str]]:
        """Load a settings profile from a JSON file.

        Returns (schema, issues). Missing files return defaults with an issue.
        """
        issues: List[str] = []
        try:
            with Path(path).open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except FileNotFoundError:
            issues.append("file not found; using defaults")
            return SettingsService.defaults(), issues
        except json.JSONDecodeError as exc:
            issues.append(f"invalid JSON: {exc}")
            return SettingsService.defaults(), issues

        return SettingsService.from_profile_dict(raw)

    @staticmethod
    def save_json(path: Path, settings: SettingsSchema) -> None:
        """Save a settings profile to a JSON file (pretty-printed)."""
        profile = SettingsService.to_profile_dict(settings)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with Path(path).open("w", encoding="utf-8") as fh:
            json.dump(profile, fh, indent=2, ensure_ascii=False)
