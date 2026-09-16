# Contributing

Open an issue describing inputs (dimensions/formats, not private photos), expected vs actual behavior, configuration and dependency versions. Redact user paths and GPS/EXIF metadata before sharing diagnostics.

Run `python -m unittest discover -s tests -v`. For layout/theme changes, render 4:3 and 9:16, light and dark palettes, and at least one multi-photo ending. Inspect actual output: slot mask, tray boundaries, green flash/red completion, crop/fit, ending bounds and audio timing.

Add parameter validation and a focused regression test for each demonstrated bug. Keep media normalization, geometry, timing, themes and CLI orchestration separate. Preserve the portable configuration contract or introduce a new version with migration guidance. Do not silently upgrade the renderer during normal user renders; dependency upgrades require documented checks.
# Packaging

Run `python scripts/package_release.py --output dist/printer-effect.zip` to produce a source-only archive. It excludes rendered projects, private inputs in output folders, virtual environments and node_modules. Review any new example media before release.
