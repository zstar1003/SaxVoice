# SaxVoice

简洁的萨克斯曲谱库。按分类选曲、搜索曲目，切换高音与中音版本，在浏览器中全屏阅读，或下载 A4 曲谱练习。

[在线曲库](https://xdxsb.top/SaxVoice/)

## 功能

- 中文、英文、拼音、作曲家与分类搜索，支持折叠的两级目录。
- 降 B 高音与降 E 中音版本，各自标明记谱调、实音调与音区。
- 一键全屏：默认适宽显示，可切换整页；保留翻页、打印与分享，按 Esc 退出。不支持原生全屏的浏览器使用窗口全屏阅读。
- A4 矢量 PDF、可编辑 MusicXML 和谱页预览。
- 桌面侧栏、手机选曲抽屉、专注阅读与当前页分享链接。
- 金色萨克斯图标，支持浏览器标签与 iOS 主屏幕。

## 曲库

当前 **53 首曲目、106 个乐器版本、112 页 A4 曲谱**。包括流行与当代、器乐与古典、民谣与传统、节庆与颂歌、入门练习，共 5 个一级分类、13 个二级分组。

| 精选曲目 | 本站版本 |
| --- | --- |
| [赛马](https://xdxsb.top/SaxVoice/?song=saima) | 开篇主题，42 小节 |
| [名侦探柯南](https://xdxsb.top/SaxVoice/?song=detective-conan) | 经典主主题段及收束，15 小节 |
| [天空之城](https://xdxsb.top/SaxVoice/?song=carrying-you) | 主题两段，含弱起共 33 小节 |
| [永远同在](https://xdxsb.top/SaxVoice/?song=always-with-me) | 《千与千寻》主旋律一遍，含弱起共 33 小节 |
| [圣诞快乐，劳伦斯先生](https://xdxsb.top/SaxVoice/?song=merry-christmas-mr-lawrence) | 三连音前奏与首段主题，32 小节 |
| [回家 / Going Home](https://xdxsb.top/SaxVoice/?song=going-home) | 开篇萨克斯主题，21 小节 |
| [无心快语 / Careless Whisper](https://xdxsb.top/SaxVoice/?song=careless-whisper) | 萨克斯开场独奏，17 小节 |
| 奇异恩典、绿袖子、友谊地久天长 | 传统旋律 |
| 欢乐颂、勃拉姆斯摇篮曲 | 古典主题 |
| 小猴子转圈圈、鸭子抖毛、鬼鬼祟祟 | 热门 BGM 主题 |

本站提供单声部萨克斯旋律谱。各曲的编选范围、音区处理与参考版本在曲谱信息中说明；主题版按段落编选，不作为完整录音的伴奏时间轴。来源与版本记录见 [library-sources.md](docs/library-sources.md)。

高音谱实音低大二度，中音谱实音低大六度；中音按旋律选择合适八度。制谱校验各小节时值、延音线、临时记号、移调与 B♭3–F♯6 常规记谱音域。

## 本地预览与部署

原生 HTML/CSS/JavaScript，无前端运行依赖。

```sh
python3 -m http.server 8000 --directory site
```

GitHub Pages 通过 [GitHub Actions](.github/workflows/pages.yml) 发布 `site/`。推送 `main` 后自动部署，在线站点使用账号已有自定义域名。

## 新增曲目与制谱

1. 在 [scores/library.json](scores/library.json) 填写曲名、实音旋律、拍号、调号、时值、编选范围和参考版本。
2. 在 [scores/categories.json](scores/categories.json) 将曲目 ID 加入二级分组。
3. 生成乐器版本并运行校验；前端自动从 [site/catalog.json](site/catalog.json) 加载。

Python 依赖：`verovio`、`cairosvg`、`pypdf`、`reportlab`；预览渲染使用 Poppler `pdftoppm`。

```sh
python scripts/build_library.py
python scripts/build_library.py --rebuild going-home # 重新排版指定曲目
python scripts/validate_library.py
```

音符示例：`F#4:e.` 为附点八分音符，`Bb4:q` 为降 B 四分音符，`R:e` 为八分休止符；`G4:h.~` 开始延音线，`G4:h_` 结束延音线。时值使用 `w/h/q/e/s/t`，其中 `t` 为三十二分音符；`e3` 表示八分音符三连音，连续三个为一组。弱起与尾小节以 ticks 声明，四分音符为 4 ticks。未改变记谱的现有文件会直接复用。

中文 PDF 字体可通过 `SAXVOICE_SCORE_FONT` 指定，Poppler 路径可通过 `SAXVOICE_PDFTOPPM` 指定。乐谱符号采用 Verovio Leipzig 字形，许可见 [Leipzig license](site/scores/juebieshu/Leipzig-LICENSE.txt)。

## 许可与隐私

网站代码采用 [MIT](LICENSE)；第三方音乐与曲谱依据各自发布授权或许可，记录见 [sources.md](docs/sources.md) 与 [library-sources.md](docs/library-sources.md)。MIT 不覆盖第三方作品。

网站源码没有分析脚本、外部播放器或远程字体，谱页与文件从本站加载。域名托管层可能注入其独立脚本。
