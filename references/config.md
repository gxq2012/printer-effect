# Configuration v1

JSON paths resolve relative to the config file. CLI inputs resolve relative to the current directory. CLI flags override JSON; `--aspect` clears JSON `canvas`, `--duration` clears per-file print durations. Unknown keys and nonfinite numbers are errors. Internal `computed_duration` is not an input setting.

| Key | Default / accepted values |
| --- | --- |
| version | 1 |
| inputs | File paths, folders, or per-file objects; 1–100 items |
| cover | File already in inputs, moved to the front |
| aspect_ratio | 9:16; also 4:3, 3:4, 1:1, 16:9 |
| canvas | Optional explicit [width,height], even integers 320–4096; overrides ratio |
| style | modern / retro / instant |
| color | ivory, cream, mint, pink, blue, black, silver, red, white, matcha, light-blue or #RRGGBB |
| background | #eee9df; named color or #RRGGBB |
| content_width | .9; content box/canvas width, not guaranteed visible-image width |
| paper_border | 4 landscape, 16 portrait; 0–60 design pixels |
| machine_height | Printer: 194 landscape/square, 333 portrait (194–400); instant: 360 landscape/square, 842.4 portrait (194–900) |
| camera_width | Instant-only fraction .25–.96; overrides machine_height; CLI accepts 90% |
| camera_appearance | photo for bundled camera colors; rendered for other colors |
| develop_seconds | Instant 2.5s, printer 0; range 0–15 |
| flash | true; instant-camera flash, false disables it |
| fit | contain (complete image), cover (crop to fill) |
| position | [.5,.5]; cover crop focal position, x/y in 0..1 |
| duration | Optional total seconds; mutually exclusive with print_seconds |
| print_seconds | Single 8s; multi first 4.8s, following 2.4s; per-file override |
| opening | .6s |
| printed_hold | .5s, per item |
| travel | .75s to staging row |
| final_hold | 3s |
| ending | hold, row, flyout, stack, grid, snowflake; collage is legacy alias |
| feed | stepped / smooth |
| sound | true; synthesized printer motor during each print |
| sound_volume | .55; 0..1 |
| sound_file | Optional local replacement audio, looped/trimmed to each print |
| source_audio | false; retain video's chosen excerpt audio if true |
| complete_color | #ee3838, completion LED |
| blink_period | .54 seconds; .3–3 |
| fps | 30, integer 15–60, used for preprocessing AND render |
| quality | high, standard, draft |
| cache | true; content-hash cache, disable to troubleshoot |
| export_cover | true |
| title | HTML project title, not automatically printed caption |

All layout measurements use a 1440-wide design plane. Machine/tray width is 1380; paper must fit within the slot. Oversized border+width combinations are rejected. contain preserves source ratio; layout-report.json gives actual visible width. More than 12 photos in row/stack/snowflake become paginated grid with a note. Stack intentionally overlaps photos; flyout shows each individually. More than 100: split into videos.

Per-file video example:

```json
{"path":"clip.mp4","play_seconds":3,"media_start":0.5,"crop":[1260,970,620,230]}
```

Crop coordinates apply after video rotation, in source pixels: width,height,x,y. Crop is optional; do not copy example numbers blindly. If play time exceeds remaining source duration, last frame holds. Audio plays only over the available excerpt. Original source audio is off unless requested.

## Files and diagnostics

- `printer-config.json`: portable editable config, uses original media copies under assets/.
- `timing.json`: exact print/play/ending times.
- `layout-report.json`: geometry and fit notes.
- `render-report.json`: measured output metadata.
- `check.log`, `render.log`, `snapshots/`: diagnostics.
- `renders/printer-effect.mp4`, `renders/cover.jpg`: deliverables.

`--revision` creates a new numbered directory rather than deleting an existing output. Builds write to a temporary sibling and rename only on success. A failed render leaves its project/logs for diagnosis. Cache location defaults to ~/.cache/printer-effect, configurable with PRINTER_EFFECT_CACHE; it contains private media derivatives, so do not commit or share it. Delete that dedicated cache to clear it.


## Instant geometry and timing

The design plane is 1440 pixels wide. Instant camera width = machine_height / 0.65; a camera_width override sets height to camera_width × 1440 × 0.65. Body and lens are never stretched independently. Paper is capped to the slot. A single print can lift the camera and slot mask together to preserve paper width when vertical space is limited; multi-photo mode retains bounded staging geometry.

Capture adds 0.45s per image; development follows complete ejection, then printed_hold, optional source-video play and ending. `duration` includes all phases. A short request may be impossible even with minimum 0.5s feed per item.

Photo assets support ivory, pink, matcha, white and light-blue/blue (including their matching hex values). JSON `camera_appearance:"rendered"` selects the vector design. An unsupported photo/color combination is rejected. CLI `--color` reselects the appropriate appearance. Chinese aliases: 粉色、抹茶、白色、淡蓝色.

`--machine-height` clears a saved camera_width when no --camera-width is supplied. `--color` clears a saved camera_appearance. `--camera-width` takes precedence if both width and height are supplied.

## CLI reference

Run `python scripts/cli.py --help` and `python scripts/cli.py render --help` for the exact current flags. JSON-only controls include develop_seconds, flash, camera_appearance, canvas, opening, printed_hold, travel, final_hold, complete_color, blink_period, position, export_cover and per-file playback settings.

## Date/time postmark / 日期时间邮戳

Both printers and instant cameras add a postal-style date/time mark by default. A new run captures Beijing date and time (seconds), fixed UTC+8 regardless of host timezone; no timezone label is printed once; preview and render use the same value. Saved configs preserve it for reproducible revisions. Remove timestamp_text from a saved config to capture a new time. `--no-timestamp` or JSON `timestamp:false` disables it. JSON `timestamp_text` accepts up to 100 characters, with `|` separating two display lines. This is a decorative printed-at time, not the original photo capture date or an official postal mark.

打印机和拍立得默认添加邮戳式日期时间：本次生成时的北京时间日期和时分秒（固定东八区，不受电脑时区影响，画面不显示UTC）。预览与导出固定一致；旧配置保留原值，删除timestamp_text后可获取新时间。`--no-timestamp`或JSON `timestamp:false`可关闭。`timestamp_text`最多100字符，使用`|`分成两行。它表示生成时间，不是照片拍摄时间，也不是官方邮戳。
