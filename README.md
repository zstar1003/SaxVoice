# SaxVoice

《诀别书》降 B 高音萨克斯曲谱阅读、下载和打印网站。

- [网站](https://xdxsb.top/SaxVoice/)
- [3页A4矢量PDF](https://xdxsb.top/SaxVoice/scores/juebieshu/juebieshu-soprano-bb-a4.pdf)
- [保留原谱音区的移调对照版](https://xdxsb.top/SaxVoice/scores/juebieshu/juebieshu-soprano-bb-reference-a4.pdf)
- [可编辑MusicXML](https://xdxsb.top/SaxVoice/scores/juebieshu/juebieshu-soprano-bb.musicxml)

GitHub Pages入口：https://zstar1003.github.io/SaxVoice/ （跳转至账号原有自定义域名。）

## 曲谱版本

当前是降B高音萨克斯单声部旋律编配：E小调记谱（一个升号），实音D小调。109小节、27行，重新录入音符、节奏及延音线，排成3页A4矢量PDF。当前谱页不含截图或背景残留。阅读器支持翻页、放大和全部3页打印。

默认版将49–64小节降低八度；这是一项明确标注的演奏音区调整。对照版保留输入旋律音区，两版具有相同音级、时值和小节顺序。没有为了缩短页数删除过渡或重复段落。

对照目标为[邓垚《诀别书》原发行条目](https://music.163.com/song?id=2038191895)，平台元数据时长246971毫秒，钢琴署名邓垚、编曲署名韦伟。局部旋律检查使用公开的完整版录音；尚未完成原发行母带和钢琴各声部的全曲人工逐音校对，不承诺钢琴逐音一致。详见[校对说明](docs/music-review.md)。

本次公开发布依据用户在会话中确认取得授权。曲谱和音乐作品不适用网站代码的MIT许可。[发布依据](docs/sources.md)。仓库不发布原视频或伴奏音频。

## 本地预览与部署

网站是原生HTML/CSS/JavaScript，无运行依赖或构建步骤。

```sh
python3 -m http.server 8000 --directory site
```

打开 http://localhost:8000 。推送至main后，[GitHub Actions](.github/workflows/pages.yml)自动部署site目录。

## 重新制谱

[scores/juebieshu.json](scores/juebieshu.json)保存结构化输入音符、时值及八度处理说明；[scripts/build_score.py](scripts/build_score.py)转为降B MusicXML，用Verovio生成矢量五线谱，再合成A4 PDF。需要Python及verovio、cairosvg、pypdf、reportlab和系统pdftoppm。

```sh
python scripts/build_score.py
```

输入音符保留原记谱的两个升号，脚本统一上移纯四度得到降B高音萨克斯记谱；默认版再将49–64小节降低八度。导出的MusicXML已是降B谱，并明确设置乐器实音低大二度。脚本检查每小节4拍和延音线两端音高，生成默认版、对照版以及3张网页预览。旧PDF地址仍指向新版。

PDF中文标题字体以子集形式嵌入。macOS默认使用STHeiti Light；其他系统可设置SAXVOICE_SCORE_FONT。乐谱符号使用Verovio的Leipzig字形，相关字体许可见[Leipzig license](site/scores/juebieshu/Leipzig-LICENSE.txt)。

## 许可与隐私

网站代码采用[MIT](LICENSE)，音乐与曲谱权利归原权利人。没有分析脚本、Cookie、远程字体或外部播放器；PDF和谱页均从本站加载。
