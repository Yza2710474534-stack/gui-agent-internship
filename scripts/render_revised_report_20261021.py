"""Render the revised report and materialize its contents page numbers."""
import json
import os
import re
import subprocess
from pathlib import Path

from docx import Document
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path('/Users/ziang/.cache/codex-runtimes/codex-primary-runtime')
PY = RUNTIME/'dependencies/python/bin/python3'
RENDER = Path('/Users/ziang/.codex/plugins/cache/openai-primary-runtime/documents/26.1015.12040/skills/documents/render_docx.py')
REPORT = ROOT/'output/docx/结项报告.docx'
OUT = ROOT/'tmp/week8/revision_20261021/render'


def norm(s): return re.sub(r'\s+', '', s)


def render(env):
    subprocess.run([str(PY),str(RENDER),str(REPORT),'--output_dir',str(OUT),'--emit_pdf','--dpi','105'],env=env,check=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    conf=OUT.parent/'fonts.conf'
    fonts=RUNTIME/'dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fonts/truetype'
    conf.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>'
                    '<dir>/System/Library/Fonts/Supplemental</dir>'+f'<dir>{fonts}</dir>'
                    '<cachedir>/private/tmp/final-report-20261021-fontcache</cachedir></fontconfig>')
    env={**os.environ,'FONTCONFIG_FILE':str(conf)}
    render(env)
    pdf=PdfReader(OUT/'结项报告.pdf');doc=Document(REPORT); entries={}
    lines=[{norm(line) for line in page.extract_text().splitlines()} for page in pdf.pages]
    for p in doc.paragraphs:
        if '\t' not in p.text or not p.text.rsplit('\t',1)[1].isdigit(): continue
        title=p.text.rsplit('\t',1)[0]
        found=[i+1 for i,page in enumerate(lines) if i>=2 and norm(title) in page]
        assert found, title
        entries[title]=found[0]
        p.text=title+'\t'+str(found[0])
    assert len(entries)==14
    doc.save(REPORT)
    render(env)
    final=PdfReader(OUT/'结项报告.pdf')
    for title,n in entries.items():
        assert norm(title) in norm(final.pages[n-1].extract_text()),title
    summary={'pages':len(final.pages),'contents':entries,'render_tool':str(RENDER),
             'renderer':'Bundled LibreOffice with explicit system CJK fonts',
             'page_images':[str((OUT/f'page-{i+1}.png').relative_to(ROOT)) for i in range(len(final.pages))]}
    p=ROOT/'output/archive/20261021/report_layout.json';p.write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps({'pages':len(final.pages),'contents':entries},ensure_ascii=False,indent=2))


if __name__=='__main__': main()
