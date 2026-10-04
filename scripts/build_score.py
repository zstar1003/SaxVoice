"""Build the authorized video score as four A4 pages.

Usage: bundled-python scripts/build_score.py path/to/source.mp4
Requires ffmpeg, numpy, opencv-python, reportlab and pdftoppm.
The video remains local; only the extracted score and PDF are published.
"""
from pathlib import Path
import json
import os
import subprocess
import sys

import cv2
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "output/video/bands"
DEST = ROOT / "site/scores/juebieshu"
BOUNDARIES = [0, 10, 20, 30, 39, 49, 59, 67, 76, 84, 93, 101, 109,
              118, 127, 136, 144, 153, 161, 169, 178, 186, 195, 203,
              211, 220, 228, 242]
SOURCE = "https://www.bilibili.com/video/BV18t421W7ev/"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: build_score.py path/to/source.mp4")
    TMP.mkdir(parents=True, exist_ok=True)
    DEST.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", sys.argv[1],
        "-vf", "fps=1,crop=1140:139:70:581", str(TMP / "%03d.png")
    ], check=True)
    rows = []
    for index, (start, end) in enumerate(zip(BOUNDARIES, BOUNDARIES[1:])):
        # Temporal median suppresses the moving scenery beneath the translucent score.
        frames = [cv2.imread(str(TMP / f"{second+1:03d}.png"), cv2.IMREAD_GRAYSCALE)
                  for second in range(start + 2, end - 1)]
        if any(frame is None for frame in frames):
            raise RuntimeError(f"Missing frame in system {index+1}")
        image = np.median(np.stack(frames), axis=0)
        image = np.clip((image - 90) * 255 / 80, 0, 255).astype(np.uint8)[4:134]
        # Remove the scene boundary and the next system's clipped preview at the edges.
        image[:4] = 255
        image[-4:] = 255
        filename = f"row-{index+1:02d}.png"
        cv2.imwrite(str(DEST / filename), image)
        rows.append({"system": index+1, "firstMeasure": index*4+1,
                     "startSecond": start, "endSecond": end, "file": filename})

    font_path = os.environ.get("SAXVOICE_SCORE_FONT", "/System/Library/Fonts/STHeiti Light.ttc")
    if not Path(font_path).is_file():
        raise RuntimeError("Set SAXVOICE_SCORE_FONT to a Chinese TrueType font to embed in the PDF")
    pdfmetrics.registerFont(TTFont("ScoreChinese", font_path, subfontIndex=0))
    pdf_path = DEST / "juebieshu-saxophone-a4.pdf"
    pdf = canvas.Canvas(str(pdf_path), pagesize=A4, pageCompression=1)
    pdf.setTitle("诀别书 - 萨克斯独奏谱 - A4视频谱面整理版")
    pdf.setAuthor("作曲：邓垚；视频谱源：马克也有Club；排版：SaxVoice")
    pdf.setSubject("27行谱面，4页A4；依据用户确认的授权整理发布")
    width, height = A4
    pages = []
    for page_index in range(4):
        group = rows[page_index*7:(page_index+1)*7]
        first = group[0]["firstMeasure"]
        last = 109 if page_index == 3 else group[-1]["firstMeasure"]+3
        pdf.setFillColorRGB(.18, .18, .18)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(12*mm, height-14*mm, "SAXVOICE / SHEET MUSIC")
        pdf.drawRightString(width-12*mm, height-14*mm, f"A4 / {page_index+1} of 4")
        pdf.setFont("ScoreChinese", 25)
        pdf.drawCentredString(width/2, height-27*mm, "诀别书")
        pdf.setFont("ScoreChinese", 10)
        pdf.drawCentredString(width/2, height-35*mm, "萨克斯独奏谱 · 视频谱面整理版")
        pdf.setFont("ScoreChinese", 9)
        pdf.drawString(12*mm, height-44*mm, "作曲：邓垚    视频谱源：马克也有Club")
        pdf.drawRightString(width-12*mm, height-44*mm, f"第 {first}-{last} 小节")
        pdf.setStrokeColorRGB(.7, .7, .7)
        pdf.setLineWidth(.4)
        pdf.line(12*mm, height-47*mm, width-12*mm, height-47*mm)

        image_width = width-24*mm
        image_height = image_width*130/1140
        for row_index, row in enumerate(group):
            top = height-(52+31*row_index)*mm
            pdf.drawImage(ImageReader(str(DEST/row["file"])), 12*mm,
                          top-image_height, width=image_width, height=image_height)

        pdf.setFont("ScoreChinese", 8)
        if page_index == 2:
            pdf.drawString(12*mm, 29*mm,
                           "说明：第63小节速度标识上沿在原视频中被裁切，数字可辨为114，音符按原谱保留。")
        pdf.setStrokeColorRGB(.7, .7, .7)
        pdf.line(12*mm, 23*mm, width-12*mm, 23*mm)
        pdf.drawString(12*mm, 18*mm, "视频谱源：马克也有Club · 排版整理：SaxVoice · 曲谱及音乐版权归原权利人。")
        pdf.setFont("Helvetica", 7)
        pdf.drawString(12*mm, 13*mm, SOURCE)
        pdf.linkURL(SOURCE, (12*mm, 12*mm, 125*mm, 16*mm), relative=0)
        pdf.drawRightString(width-12*mm, 13*mm, f"SaxVoice | {page_index+1}/4")
        pdf.showPage()
        pages.append({"number": page_index+1, "firstMeasure": first, "lastMeasure": last,
                      "image": f"page-{page_index+1}.png"})
    pdf.save()
    subprocess.run(["pdftoppm", "-scale-to", "1800", "-png", "-r", "160",
                    str(pdf_path), str(DEST/"page")], check=True)
    manifest = {"title": "诀别书", "composer": "邓垚", "sourcePublisher": "马克也有Club",
                "sourceUrl": SOURCE, "createdDate": "2026-10-04", "pages": pages,
                "systems": rows, "pdf": pdf_path.name, "paper": "A4",
                "permissionBasis": "用户在当前会话确认已联系发布者并取得本次整理与发布授权。",
                "qualityNote": "视频720P谱面整理，保留原记谱；第63小节速度标识原视频上沿裁切。"}
    (DEST/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    print(f"Created {pdf_path}: 4 A4 pages, 27 systems")


if __name__ == "__main__":
    main()
