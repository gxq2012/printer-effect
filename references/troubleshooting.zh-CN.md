# 常见问题

[English](troubleshooting.md) · [中文首页](../README.zh-CN.md)

| 问题 | 处理方法 |
| --- | --- |
| 找不到Python／npm／FFmpeg／ffprobe | 安装对应依赖后重新打开终端，运行doctor；Node需22以上 |
| 提示缺少GSAP | 在技能目录运行python scripts/cli.py setup，根据锁文件安装 |
| Pillow或HEIC错误 | 用同一个虚拟环境Python安装requirements和执行渲染；HEIC依赖pillow-heif，macOS可回退sips |
| 浏览器运行环境下载失败 | 检查网络和check.log；首次渲染可能下载依赖，不是完全离线安装 |
| 输出目录已存在 | 换--output，或添加--revision；系统不会覆盖旧成品 |
| 找不到图片 | 空格路径加引号；JSON内路径相对于JSON所在目录 |
| 总时长太短 | 增加--duration，减少照片、显影或停留时长，或省略duration自动规划 |
| 下方空间不足 | 缩小camera-width／machine_height，选择竖屏，或减小边框；单图拍立得会自动上移，多图仍需预留队列空间 |
| 照片没有达到设定宽度 | width是内容区域目标；原图比例、出纸口也会限制。查看layout-report.json；flyout可放大展示 |
| 图片被裁切 | 使用--fit contain；cover表示允许裁切 |
| 没声音 | 检查播放器静音、sound和音量；--silent关闭效果声，视频原声需单独--source-audio |
| 不要闪光 | JSON设置flash:false；快门声仍保留，除非sound:false |
| 自定义颜色不能使用photo模式 | 设置camera_appearance为rendered；拟真素材仅支持文档列出的颜色 |
| 渲染失败 | 查看输出目录check.log、render.log；分享日志前去掉私人路径，不要连原始照片一起上传 |

build只建项目，不代表视频完成。preview会新建项目。手动改HTML后在生成项目运行固定版本的npm脚本；修改参数则用旧printer-config.json和新输出目录重建。

## 能力范围

这是确定性的动画效果，不是实体打印机驱动或AI人物动作生成模型。不生成配音、不自动发布社交平台、不自动上传GitHub。雪花指照片拼贴。已验证平台见首页；配置CI不代表已在远程运行通过。
