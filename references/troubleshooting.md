# Troubleshooting

[中文](troubleshooting.zh-CN.md) · [README](../README.md)

| Symptom | Action |
| --- | --- |
| Missing Python, npm, FFmpeg or ffprobe | Install the prerequisite and reopen the terminal; run `python scripts/cli.py doctor`. Node must be 22+ |
| GSAP missing | Run `python scripts/cli.py setup` inside the skill folder; it runs npm ci from the lockfile |
| Pillow/HEIC import error | Use the same virtual-environment Python for pip and render. Install requirements; HEIC uses pillow-heif, with macOS sips fallback |
| Browser/runtime download fails | Check network access and the generated check.log. Initial rendering may download dependencies; do not assume offline operation |
| Output exists | Choose another --output or add --revision; existing files are intentionally protected |
| Input not found | Quote spaces; resolve JSON paths relative to its directory, not the terminal |
| Duration too short | Increase --duration, reduce images/develop_seconds/holds, or omit duration for automatic planning |
| No room below machine | Reduce --camera-width or machine_height, choose portrait, or reduce borders. Single instant photos lift the camera automatically; multi-photo staging has tighter limits |
| Photo looks smaller than width setting | Width is a content-box target. Original ratio and physical output slot also matter; inspect layout-report.json. Use flyout to enlarge the completed print |
| Crop is unwanted | Use --fit contain. Do not use cover unless intentional |
| No sound | Check player mute, sound:true and volume. --silent mutes effects; source audio is separately enabled with --source-audio |
| Flash too strong | Set flash:false in JSON; shutter sound remains unless sound:false |
| Can't use custom color in photo mode | Choose camera_appearance:rendered; photo assets exist only for documented palettes |
| Render fails | Inspect check.log/render.log in the output project. Share redacted logs and config, not original private inputs |

`build` is not a completed MP4. `preview` creates a new project. To render direct HTML edits, use the generated project's pinned npm scripts. For a settings revision, use --config pointing to the previous printer-config.json and a new output directory.

## Scope

This is a deterministic media effect, not a physical printer driver or AI image-to-video model. It does not animate subjects inside still photos, generate narration, publish to social networks or upload to GitHub. Snowflake means photo collage. Tested platform claims are listed in README; the configured CI workflow is not evidence that remote jobs have run.
