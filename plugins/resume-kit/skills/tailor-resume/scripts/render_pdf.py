#!/usr/bin/env python3
"""Turn a resume markdown file into an ATS-safe PDF using Chrome or Edge.

Usage:
    python3 scripts/render_pdf.py "<resume.md>"            -> writes <resume>.pdf next to it
    python3 scripts/render_pdf.py "<resume.md>" "<out.pdf>"
    python3 scripts/render_pdf.py --pages-only "<resume.md>"   -> page count only, no PDF kept

Prints one line of JSON: {"pdf": path, "pages": N}  (or {"error": ...}).
Single column, real text (selectable, readable by applicant tracking systems),
no tables or images. Uses only the Python standard library plus the Chrome
or Microsoft Edge already installed on the computer.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CSS = """
@page {
  size: Letter;
  margin: 0.75in 1in 0.75in 1in;
  @bottom-center { content: "%(name)s  \\2022  Page " counter(page) " of " counter(pages);
                   font: 8.5pt Calibri, Carlito, Arial, sans-serif; color: #666; }
}
body { font: 10pt/1.27 Calibri, Carlito, "Helvetica Neue", Arial, sans-serif; color: #111; margin: 0; }
h1 { font-size: 20pt; letter-spacing: .5px; margin: 0 0 2pt; }
.headline { font-size: 12pt; font-weight: 600; margin: 0 0 3pt; }
.contact { font-size: 9.5pt; margin: 0 0 6pt; padding-bottom: 5pt; border-bottom: 1px solid #333; }
h2 { font-size: 11pt; letter-spacing: .4px; margin: 9pt 0 4pt; padding-bottom: 2pt;
     border-bottom: 1px solid #333; break-after: avoid; }
h3 { font-size: 10.5pt; margin: 7pt 0 0; break-after: avoid; }
.row { display: flex; justify-content: space-between; gap: 12pt; }
.title { font-weight: 700; margin: 0 0 2pt; break-after: avoid; }
p { margin: 0 0 4pt; text-align: justify; }
p.desc { font-style: italic; }
ul { margin: 0 0 5pt; padding-left: 16pt; }
li { margin: 0 0 2pt; text-align: justify; }
li, p { break-inside: avoid; }
"""


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def split_row(text):
    """'LEFT | RIGHT' -> a left/right row (text order stays left then right)."""
    left, _, right = text.rpartition(" | ")
    if not left:
        return inline(text)
    return f'<span>{inline(left)}</span><span>{inline(right)}</span>'


def md_to_html(md):
    lines = md.splitlines()
    out, in_ul, name, head_lines = [], False, "", 0

    def close_ul():
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for raw in lines:
        line = raw.rstrip()
        if not line:
            close_ul()
            continue
        if line.startswith("# "):
            name = line[2:].strip()
            out.append(f"<h1>{inline(name)}</h1>")
            head_lines = 1
            continue
        if head_lines and not line.startswith("#"):
            # the two lines under the name: headline, then contact line
            cls = "headline" if head_lines == 1 else "contact"
            out.append(f'<p class="{cls}">{inline(line)}</p>')
            head_lines = head_lines + 1 if head_lines == 1 else 0
            continue
        head_lines = 0
        if line.startswith("## "):
            close_ul()
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("### "):
            close_ul()
            out.append(f'<h3 class="row">{split_row(line[4:])}</h3>')
        elif line.startswith("- "):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(line[2:])}</li>")
        elif line.startswith("**") and line.endswith("**") and " | " in line and ":**" not in line:
            close_ul()
            out.append(f'<div class="title row">{split_row(line[2:-2])}</div>')
        elif line.startswith("*") and not line.startswith("**") and line.endswith("*"):
            close_ul()
            out.append(f'<p class="desc">{inline(line[1:-1])}</p>')
        else:
            close_ul()
            out.append(f"<p>{inline(line)}</p>")
    close_ul()
    css = CSS % {"name": name.title().replace('"', "")}
    return ("<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{html.escape(name.title())} - Resume</title><style>{css}</style></head>"
            f"<body>{''.join(out)}</body></html>")


def find_browser():
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for base in filter(None, [os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"),
                              os.environ.get("LOCALAPPDATA")]):
        candidates += [os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                       os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe")]
    candidates += [shutil.which(n) for n in ("google-chrome", "chromium", "chromium-browser",
                                             "chrome", "msedge", "microsoft-edge")]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


def count_pages(pdf_bytes):
    return len(re.findall(rb"/Type\s*/Page(?!s)", pdf_bytes))


def main():
    args = sys.argv[1:]
    pages_only = "--pages-only" in args
    args = [a for a in args if a != "--pages-only"]
    if len(args) not in (1, 2):
        print(__doc__)
        sys.exit(2)
    src = Path(args[0]).resolve()
    scratch = tempfile.mkdtemp() if pages_only else None
    if pages_only:
        out = Path(scratch) / "length-check.pdf"
    else:
        out = Path(args[1]).resolve() if len(args) == 2 else src.with_suffix(".pdf")
    browser = find_browser()
    if not browser:
        print(json.dumps({"error": "Chrome or Microsoft Edge was not found. The tailored markdown "
                                   "is ready; install Chrome to make the PDF."}))
        sys.exit(1)
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "resume.html"
        page.write_text(md_to_html(src.read_text(encoding="utf-8")), encoding="utf-8")
        cmd = [browser, "--headless=new", "--disable-gpu", "--no-first-run",
               f"--user-data-dir={Path(tmp) / 'profile'}", "--no-pdf-header-footer",
               f"--print-to-pdf={out}", page.as_uri()]
        if out.exists():
            out.unlink()
        # Headless Chrome sometimes stays alive after printing, so wait for a
        # finished PDF (ends with %%EOF) and then close the browser ourselves.
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.time() + 90
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            if out.exists() and out.read_bytes().rstrip().endswith(b"%%EOF"):
                time.sleep(0.5)
                break
            time.sleep(0.5)
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
    if not out.exists():
        print(json.dumps({"error": "The browser did not produce a PDF.", "browser": browser}))
        sys.exit(1)
    pages = count_pages(out.read_bytes())
    if pages_only:
        shutil.rmtree(scratch, ignore_errors=True)
        print(json.dumps({"pages": pages}))
    else:
        print(json.dumps({"pdf": str(out), "pages": pages}))


if __name__ == "__main__":
    main()
