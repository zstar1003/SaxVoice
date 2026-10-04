# SaxVoice

一个轻量、开源的萨克斯谱源书架，首个收录曲目是邓垚的《诀别书》。

**网站：** https://zstar1003.github.io/SaxVoice/

## 内容与许可

当前公开的是三处 Bilibili 原始谱源链接、发布者署名和选谱指南，**没有上传或提供完整曲谱、视频及伴奏文件**。三处原来源均标记禁止未经授权转载；完整曲谱的获取方式、价格及具体萨克斯版本以原作者说明为准。来源核验日期为 2026-10-04，详细记录见 [docs/sources.md](docs/sources.md)。

本仓库的原创网站代码、排版和文案采用 [MIT License](LICENSE)。外部音乐作品、曲谱、视频、伴奏及相关权利不属于此代码许可的范围。

## 本地预览

网站使用原生 HTML、CSS 和 JavaScript，无依赖、无构建步骤。

```sh
python3 -m http.server 8000 --directory site
```

打开 http://localhost:8000 。

## GitHub Pages 部署

在仓库 **Settings → Pages → Source** 选择 **GitHub Actions**。推送到 `main` 后，[部署工作流](.github/workflows/pages.yml) 自动发布 `site/`，也支持手动触发。使用相对资源路径，适配 `/SaxVoice/` 项目路径。

## 补充曲谱

可提交 Issue 或 Pull Request 补充原始谱源、修正来源信息。若需要托管完整谱文件，请同时提供可核验的公开传播授权，并记录作品与编配的权利人、适用乐器、记谱调性、文件来源、许可范围与署名要求。不要将“免费下载”或“个人练习”当成公开转载许可。

## 隐私

网站不使用分析脚本、远程字体、Cookie 或外部播放器。只有主动点击外部链接时才会访问 GitHub 或 Bilibili。浏览谱源详情无需外部网络请求。
