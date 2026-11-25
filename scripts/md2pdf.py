#!/usr/bin/env python3.12
"""Render the governance Markdown docs to A4 PDF using PyMuPDF Story.

Usage: md2pdf.py <input.md> <output.pdf>
No new packages required (pymupdf + markdown-it-py already installed).
"""
import re
import sys

import pymupdf as fitz
from markdown_it import MarkdownIt

REG_FONT = "/usr/share/fonts/opentype/ipaexfont-gothic/ipaexg.ttf"
BOLD_FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

CSS = """
@page { size: a4; margin: 2cm; }
@font-face { font-family: body; src: url(ipaexfont-gothic/ipaexg.ttf); font-weight: normal; }
@font-face { font-family: body; src: url(noto/NotoSansCJK-Bold.ttc); font-weight: bold; }
body { font-family: body; font-size: 10.5px; line-height: 1.55; }
h1 { font-size: 18px; margin: 0 0 10px 0; }
h2 { font-size: 14px; margin: 14px 0 6px 0; }
h3 { font-size: 12px; margin: 10px 0 4px 0; }
ul, ol { padding-left: 18px; margin: 4px 0; }
li { margin: 2px 0; }
hr { height: 1px; background: #999; margin: 10px 0; }
code { font-family: body; background: #f0f0f0; }
blockquote { margin: 4px 0 4px 12px; color: #333; }
table { border-collapse: collapse; }
td, th { border: 1px solid #999; padding: 3px 6px; }
"""


def _bold(md_text: str) -> str:
    """Convert **bold** outside code spans (CommonMark flanking rules fail for CJK)."""
    parts = re.split(r"(`[^`]*`)", md_text)
    for i, seg in enumerate(parts):
        if i % 2 == 0:  # outside code span
            parts[i] = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", seg)
    return "".join(parts)


def md_to_html(md_text: str) -> str:
    md = MarkdownIt("commonmark").enable("table")
    # GitHub task-list checkboxes -> ballot box glyph
    md_text = re.sub(r"^(\s*)- \[ \] ", r"\1- ☐ ", md_text, flags=re.M)
    md_text = re.sub(r"^(\s*)- \[x\] ", r"\1- ☑ ", md_text, flags=re.M)
    md_text = _bold(md_text)
    return md.render(md_text)


def render(md_path: str, pdf_path: str) -> None:
    with open(md_path, encoding="utf-8") as f:
        html = md_to_html(f.read())
    arch = fitz.Archive("/usr/share/fonts/opentype")
    story = fitz.Story(html=html, user_css=CSS, archive=arch)
    rect = fitz.paper_rect("a4")
    where = fitz.Rect(50, 50, rect.width - 50, rect.height - 50)
    writer = fitz.DocumentWriter(pdf_path)
    more = True
    n = 0
    while more:
        dev = writer.begin_page(rect)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
        n += 1
    writer.close()
    doc = fitz.open(pdf_path)
    doc.set_metadata({"title": pdf_path.rsplit("/", 1)[-1].removesuffix(".pdf")})
    doc.saveIncr()
    print(f"wrote {pdf_path} ({n} pages)")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
