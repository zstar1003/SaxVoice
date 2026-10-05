# SaxVoice

浅色、简洁的萨克斯曲谱阅读器。桌面侧栏选曲，手机抽屉选曲，版本说明默认折叠；支持专注阅读、中文／英文／拼音／作曲家搜索、曲目分类、乐器版本切换、翻页、放大、A4 下载与打印、当前谱页分享链接。

- [在线曲库](https://xdxsb.top/SaxVoice/)
- [《诀别书》高音版](https://xdxsb.top/SaxVoice/?song=juebieshu&instrument=soprano)
- [《诀别书》中音版](https://xdxsb.top/SaxVoice/?song=juebieshu&instrument=alto)
- [《诀别书》次中音版](https://xdxsb.top/SaxVoice/?song=juebieshu&instrument=tenor)

GitHub Pages 使用账号已有自定义域名。推送 `main` 后自动发布 `site/`。

## 曲库

当前 20 首曲目、60 个乐器版本，共 66 页 A4 矢量 PDF。每个版本均有 MusicXML 与从 PDF 渲染的网页预览。

| 曲目 | 范围 | 每个版本页数 |
| --- | --- | --- |
| 诀别书 | 109 小节完整单声部旋律，保留已确认的高音版 | 3 |
| 奇异恩典 | 完整传统旋律，含弱起与延音线 | 1 |
| 绿袖子 | 完整传统旋律，6/8 拍 | 1 |
| 友谊地久天长 | 传统主歌与副歌旋律 | 1 |
| 小星星 | 完整 24 小节旋律 | 1 |
| 两只老虎 | 完整法国轮唱旋律 | 1 |
| 欢乐颂 | 16 小节主题旋律版 | 1 |
| 摇篮曲 | 勃拉姆斯 Op.49 No.4 主题旋律 | 1 |
| 金发少女 | 16 个记谱小节的单声部旋律 | 1 |
| 安妮·劳丽 | 17 个记谱小节的单声部旋律 | 1 |
| 洛蒙德湖 | 17 个记谱小节的单声部旋律 | 1 |
| 我的邦尼 | 33 个记谱小节的单声部旋律 | 1 |
| 克莱门汀 | 17 个记谱小节的单声部旋律 | 1 |
| 故乡的亲人 | 24 个记谱小节的单声部旋律 | 1 |
| 红河谷 | 17 个记谱小节的单声部旋律 | 1 |
| 桑塔·露琪亚 | 32 个记谱小节的单声部旋律 | 1 |
| 斯卡布罗集市 | 18 个记谱小节的单声部旋律 | 1 |
| 平安夜 | 24 个记谱小节的单声部旋律 | 1 |
| 圣者的行进 | 17 个记谱小节的单声部旋律 | 1 |
| 铃儿响叮当 | 32 个记谱小节的单声部旋律 | 1 |

除《诀别书》外，十九首从公共领域历史旋律重新录入、移调与排版，未复制现代和声伴奏。参考版本与录入说明见 [来源记录](docs/library-sources.md)。这些是单声部萨克斯旋律谱。

## 乐器与音区

- 高音：降 B，MusicXML 实音低大二度。
- 中音：降 E，MusicXML 实音低大六度。
- 次中音：降 B，MusicXML 实音低大九度。此处“低音”按用户指定指 Tenor，不是 Baritone。

高音与次中音使用相同记谱音符，实际声音相差一个八度。中音移调独立生成，通常使用比高音低八度的实音音区；部分曲目的中音版为避免超出低音域，采用与高音版相同的实音八度，具体音区显示在曲谱信息中。网页、PDF 和 MusicXML 均正确标明各自乐器。所有版本写谱音域检查在 B♭3–F♯6 内。

《诀别书》高音 PDF 和 MusicXML 保持原文件不变。中音由该版记谱下降纯四度，记谱 B 小调；次中音沿用记谱 E 小调，实音均为 D 小调。49–64 小节的八度处理保留；高音对照版继续可下载。原发行母带及钢琴各声部尚未完成全曲逐音校对，范围见 [校对记录](docs/music-review.md)。

## 本地预览

网站为原生 HTML/CSS/JavaScript，无前端运行依赖。

```sh
python3 -m http.server 8000 --directory site
```

[GitHub Actions](.github/workflows/pages.yml) 在推送 main 后自动部署。

## 制谱与新增曲目

Python 需要 `verovio`、`cairosvg`、`pypdf`、`reportlab`，以及 Poppler 的 `pdftoppm`。

```sh
python scripts/build_score.py     # 仅在修改《诀别书》基础高音谱时执行
python scripts/build_library.py   # 生成三乐器曲库，复用音符未变的现有文件
python scripts/build_library.py --rebuild jingle-bells # 重排指定曲目
python scripts/validate_library.py
```

新增曲目追加到 [scores/library.json](scores/library.json)，填写旋律、小节、实音调号、拍号、弱起／结尾时值和来源，运行曲库脚本即可。前端从 [site/catalog.json](site/catalog.json) 加载曲目，无需逐首修改 HTML。

音符格式：`F#4:e.` 为附点八分音符，`Bb4:q` 为降 B 四分音符，`R:e` 为八分休止符，`G4:h.~` 开始延音线，`G4:h_` 结束延音线。时值使用 `w/h/q/e/s`；弱起小节及尾小节单独声明 ticks（四分音符为 4）。脚本校验小节总时值、延音线、各乐器移调、常规记谱音域及 A4 矢量文件。

默认中文字体为 macOS STHeiti Light，可用 `SAXVOICE_SCORE_FONT` 指定其他兼容 TTF/TTC。可用 `SAXVOICE_PDFTOPPM` 指定 Poppler 路径。乐谱符号使用 Verovio Leipzig 字形，许可见 [Leipzig license](site/scores/juebieshu/Leipzig-LICENSE.txt)。

## 许可与隐私

网站代码采用 [MIT](LICENSE)。音乐与曲谱发布依据见 [sources.md](docs/sources.md)，MIT 不自动覆盖第三方音乐或曲谱。网站源码不加入分析脚本、外部播放器或远程字体；谱页及文件从本站加载。域名托管层可能注入其独立脚本。
