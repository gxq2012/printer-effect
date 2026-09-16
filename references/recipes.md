# Recipes

Run with the project's virtual-environment Python. Paths are examples.

```bash
# Current classic workflow
python scripts/cli.py render photo.heic --aspect 9:16 --duration 15 --output output/photo

# Modern blue machine, smooth print, photograph lifts into the center
python scripts/cli.py render photo.jpg --aspect 4:3 --duration 15 --style modern --color blue --feed smooth --ending flyout --output output/fly

# Retro cream, folder + cover, radial photo collage
python scripts/cli.py render photos/ --cover photos/cover.jpg --style retro --color cream --ending snowflake --aspect 9:16 --output output/trip

# Grid, silent, black printer
python scripts/cli.py render photos/ --style modern --color black --ending grid --silent --output output/grid

# Rebuild last project in another aspect ratio, without touching the old output
python scripts/cli.py render --config output/trip/printer-config.json --aspect 4:3 --color mint --output output/trip --revision

# Local visual timeline preview; build-only is also available
python scripts/cli.py preview --config examples/retro-stack.json --output output/preview
```

“照片飞出来”：flyout. “叠在桌上”：stack. “整齐排版”：grid. “散落成雪花”：snowflake. Actual falling snow particles are not included; don't claim the collage is snowfall. Named colors or user-provided hex colors are independent from modern/retro style.

HEIC: automatic pillow-heif decode and orientation normalization; macOS sips fallback if decoder is missing. Images convert to sRGB PNG and cap at 4096px on the longest side for render memory, while copying originals intact. Rendering is SDR; do not promise preservation of HDR gain maps.
