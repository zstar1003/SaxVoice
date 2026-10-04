# SaxVoice

《诀别书》萨克斯曲谱阅读、下载和打印网站。

**网站：** https://xdxsb.top/SaxVoice/

**A4 PDF：** https://xdxsb.top/SaxVoice/scores/juebieshu/juebieshu-saxophone-a4.pdf

GitHub Pages 入口：https://zstar1003.github.io/SaxVoice/ （自动跳转至账号原有的自定义域名。）

## 曲谱

本版从马克也有Club发布的 [Bilibili 视频](https://www.bilibili.com/video/BV18t421W7ev/) 提取27行谱面，按原顺序整理成4页A4黑白PDF，保留音符、节奏、连线、调号及速度变化。网站支持翻页、放大阅读、PDF下载和全部四页打印。视频第63小节速度标識上沿被裁切，数字可辨为114，已在第3页标注。当前保留视频记谱，没有另行移调。

本次整理和公开发布依据用户在会话中确认已联系发布者并取得授权。该授权记录不表示向访客授予进一步转载、商业使用或再许可权。曲谱和音乐作品不在代码MIT许可范围内。[授权依据和来源记录](docs/sources.md)。仓库不发布原视频或伴奏文件。

## 本地预览

网站为原生HTML/CSS/JavaScript，无运行依赖及构建步骤。

```sh
python3 -m http.server 8000 --directory site
```

打开 http://localhost:8000 。

## 部署

GitHub Pages使用GitHub Actions。推送到main后，[部署工作流](.github/workflows/pages.yml)自动发布site目录。

## 重新生成PDF

生成脚本为[scripts/build_score.py](scripts/build_score.py)。输入相同720P视频（1280×720），需要ffmpeg、pdftoppm及Python的opencv-python、numpy、reportlab。脚本使用逐秒帧的中值清理透过谱面显示的风景，再调整黑白对比，不做音符识别或生成。已发布的27行图像、4张A4预览和PDF位于site/scores/juebieshu。

```sh
python scripts/build_score.py path/to/source.mp4
```

PDF标题字体以子集形式嵌入。macOS默认使用STHeiti Light；其他系统可通过SAXVOICE_SCORE_FONT指定允许嵌入的中文TrueType字体。视频及临时输出不提交Git。

## 许可与隐私

原创网站代码采用[MIT License](LICENSE)，曲谱权利归原权利人，授权详情见来源记录。网站不使用分析脚本、Cookie、远程字体或外部播放器；谱页从本站加载。
