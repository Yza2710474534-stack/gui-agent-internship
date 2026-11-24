"""Materialize accurate contents page numbers from the bundled renderer PDF."""
import argparse
import json
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def normalize(text):
    return re.sub(r'\s+', '', text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf', type=Path)
    args = parser.parse_args()
    path = ROOT / 'output/docx/第八周项目结项报告.docx'
    doc = Document(path)
    pages = PdfReader(args.pdf).pages
    entries = {}
    for p in doc.paragraphs:
        if '\t' not in p.text:
            continue
        label, old = p.text.rsplit('\t', 1)
        if not old.isdigit():
            continue
        found = [i + 1 for i, page in enumerate(pages) if i >= 2 and
                 normalize(label) in [normalize(line) for line in page.extract_text().splitlines()]]
        assert found, label
        entries[label] = found[0]
        p.text = label + '\t' + str(found[0])
    assert len(entries) == 14, entries
    doc.save(path)
    (ROOT / 'output/week8/contents_pages.json').write_text(json.dumps(entries, ensure_ascii=False, indent=2))
    print(json.dumps(entries, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
