# Troubleshooting

This guide lists common runtime and testing issues and how to resolve them.

## Qt platform plugin / headless tests
- Symptom: "This application failed to start because no Qt platform plugin could be initialized".
- Cause: Qt needs a platform plugin (xcb, cocoa, windows). Tests run headless.
- Fix: The test suite sets QT_QPA_PLATFORM=offscreen in tests/conftest.py. Do not override it for tests. For running the app locally with a display, ensure your OS Qt dependencies are installed.

## Offscreen rendering artifacts in tests
- Some QGraphics effects may differ under offscreen. Prefer testing logic in core/ and controllers/, and keep UI tests as smoke tests.

## SVG rendering issues
- Symptom: Parts of the puppet are missing or misaligned.
- Possible causes:
  - Missing or invalid group ids in the SVG (required by Puppet/SvgLoader).
  - viewBox anomalies or non-numeric dimensions.
- Fixes:
  - Validate the SVG with core/svg_loader.py expectations; check logs (core/logging_config.py configures formatting).
  - Try simpler assets first, then iterate.

## Assets and relative paths
- The app expects to run from the repository root so that assets/ and ui_profile.json resolve correctly.
- If running from a different working directory, resolve paths relative to the repo (see tests/conftest.py for examples using Path parents).

## Settings/profile problems
- If the UI behaves strangely after profile import or changes, reset to defaults using the Settings dialog. The profile JSON is forward-compatible; unknown fields are ignored.

## PySide6 installation on Linux
- Ensure system dependencies for Qt are installed (e.g., libxcb). If you see plugin errors, consult your distro docs.

## Getting more logs
- Logging is centralized; to increase verbosity, adjust the level passed to setup_logging in macronotron.py (e.g., DEBUG) during local runs.
