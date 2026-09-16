# 配置参数 v1

[English](config.md) · [返回中文首页](../README.zh-CN.md)

JSON 文件内的路径相对于 JSON 所在目录；命令行文件路径相对于当前目录。CLI 参数覆盖 JSON。未知字段、不合法数字会被拒绝。版本号是配置格式版本，不是软件版本。

| 字段 | 默认值、范围与含义 |
| --- | --- |
| version | 1 |
| inputs | 1–100 个文件／文件夹路径，或逐文件对象 |
| cover | inputs 已包含的文件，移到第一位 |
| aspect_ratio | 默认9:16；另有4:3、3:4、1:1、16:9 |
| canvas | 可选[宽,高]；320–4096的偶数；覆盖比例，最长边/最短边不能超过3 |
| style | modern、retro、instant |
| color | ivory、cream、mint、pink、blue、black、silver、red、white、matcha、light-blue或#RRGGBB |
| background | 默认#eee9df；背景色 |
| content_width | 默认0.9，范围0.2–0.94；内容区域目标宽度占比，对应--width |
| camera_width | 仅拍立得，0.25–0.96；机身宽度占比，对应--camera-width，可在CLI写90% |
| machine_height | 打印机横屏194、竖屏333，范围194–400；拍立得横屏360、竖屏842.4，范围194–900；camera_width优先 |
| camera_appearance | photo：拟真图片机身；rendered：绘制机身。支持的配色自动选择 |
| paper_border | 横屏4、竖屏16；0–60设计像素；拍立得额外增加55底边 |
| fit | contain完整保留；cover裁切填充 |
| position | 默认[0.5,0.5]；裁切焦点，范围0–1 |
| duration | 可选总秒数1–1800；与print_seconds互斥 |
| print_seconds | 单张默认8秒；多张第一张4.8秒，其余2.4秒；逐文件可覆盖 |
| develop_seconds | 拍立得默认2.5秒；打印机0；范围0–15 |
| flash | 默认true；拍立得闪光 |
| opening | 默认0.6秒开场 |
| printed_hold | 每张出纸／显影后停留，默认0.5秒 |
| travel | 多图移入下方队列，默认0.75秒 |
| final_hold | 最后停留3秒 |
| ending | hold、row、flyout、stack、grid、snowflake；collage为兼容别名 |
| feed | stepped分段出纸；smooth平滑出纸 |
| sound | 默认true；打印声，拍立得另有快门声 |
| sound_volume | 默认0.55，范围0–1 |
| sound_file | 可选本地出纸声音，循环／截取适配；不替换快门声 |
| source_audio | 默认false；是否保留视频片段原声 |
| complete_color | 默认#ee3838；完成灯颜色 |
| blink_period | 默认0.54秒，范围0.3–3 |
| fps | 默认30，整数15–60 |
| quality | high、standard、draft |
| cache | 默认true；素材缓存 |
| export_cover | 默认true；导出封面 |
| title | 项目标题，不是画面字幕 |

所有布局参数基于1440宽设计坐标。机身／托盘对齐规则适用于打印机；拍立得没有托盘。相机宽度=机身高度/0.65；camera_width设置高度=camera_width×1440×0.65。相纸受出纸口宽度约束。单张拍立得空间不足时相机与遮挡边界同步上移，相纸保持宽度和比例。多图使用原有的下方排布布局。

每张拍立得增加0.45秒拍摄，以及显影时长。视频在出纸、显影和printed_hold后播放。总时长涵盖所有阶段；时间过短会报错。超过12张，row／stack／snowflake切换分页网格。

## 逐文件视频配置

```json
{
  "version": 1,
  "inputs": [{"path":"clip.mp4", "media_start":0.5, "play_seconds":5}],
  "style":"instant",
  "color":"light-blue",
  "aspect_ratio":"4:3",
  "camera_width":0.9,
  "develop_seconds":2,
  "flash":true,
  "source_audio":true,
  "ending":"flyout"
}
```

可选crop为[宽,高,x,y]，单位是视频旋转校正后的像素；不应直接照搬别人的裁切数值。请求片段比源视频长时，画面保持末帧，声音只播放存在的片段。

## 修改优先级

- --aspect清除旧canvas，采用该比例的默认尺寸。
- --duration清除旧print_seconds和逐文件打印时长。
- --color重新选择对应相机外观。
- --machine-height在未同时指定--camera-width时清除旧camera_width。
- --camera-width优先于machine_height。

CLI不覆盖所有JSON字段；显影、闪光、canvas、停留时长、灯色等请在JSON中填写。查看当前命令：`python scripts/cli.py render --help`。

## 输出文件

| 文件 | 用途 |
| --- | --- |
| renders/printer-effect.mp4 | 成品视频 |
| renders/cover.jpg | 最终画面封面 |
| printer-config.json | 可移植配置，引用assets中的原始素材副本 |
| timing.json | 各阶段时间点 |
| layout-report.json | 几何布局、实际可见宽度与提示 |
| render-report.json | 实测尺寸、时长、帧率、文件大小 |
| check.log、render.log、snapshots/ | 渲染诊断 |

--revision创建新编号目录；失败渲染保留日志。缓存默认~/.cache/printer-effect，可用PRINTER_EFFECT_CACHE环境变量更改；缓存可能含私人素材衍生文件，请勿提交。

## Date/time postmark / 日期时间邮戳

Both printers and instant cameras add a postal-style date/time mark by default. A new run captures Beijing date and time (seconds), fixed UTC+8 regardless of host timezone; no timezone label is printed once; preview and render use the same value. Saved configs preserve it for reproducible revisions. Remove timestamp_text from a saved config to capture a new time. `--no-timestamp` or JSON `timestamp:false` disables it. JSON `timestamp_text` accepts up to 100 characters, with `|` separating two display lines. This is a decorative printed-at time, not the original photo capture date or an official postal mark.

打印机和拍立得默认添加邮戳式日期时间：本次生成时的北京时间日期和时分秒（固定东八区，不受电脑时区影响，画面不显示UTC）。预览与导出固定一致；旧配置保留原值，删除timestamp_text后可获取新时间。`--no-timestamp`或JSON `timestamp:false`可关闭。`timestamp_text`最多100字符，使用`|`分成两行。它表示生成时间，不是照片拍摄时间，也不是官方邮戳。
