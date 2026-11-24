"""Extend the user's current report without rebuilding or changing other weekly reports."""
import copy
import hashlib
import json
import re
from pathlib import Path

from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / 'output/archive/20261021/history/结项报告_修订前.docx'
TARGET = ROOT / 'output/docx/结项报告.docx'
SOURCE = ROOT / 'reports/week8/revision_20261021'
OUT = ROOT / 'output/archive/20261021'
REFS = [
 '[1] ZHOU S, XU F F, ZHU H, et al. WebArena A Realistic Web Environment for Building Autonomous Agents[EB/OL]. 2023. https://arxiv.org/abs/2307.13854.',
 '[2] DENG X, GU Y, ZHENG B, et al. Mind2Web Towards a Generalist Agent for the Web[EB/OL]. 2023. https://arxiv.org/abs/2306.06070.',
 '[3] NIU R, LI J, WANG S, et al. ScreenAgent A Vision Language Model driven Computer Control Agent[C/OL]. IJCAI 2024: 6433-6441. https://doi.org/10.24963/ijcai.2024/711.',
 '[4] QIN Y, YE Y, FANG J, et al. UI TARS Pioneering Automated GUI Interaction with Native Agents[EB/OL]. 2025. https://arxiv.org/abs/2501.12326.',
 '[5] SQLite. Write Ahead Logging[EB/OL]. [2026-10-21]. https://www.sqlite.org/wal.html.',
 '[6] Python Software Foundation. multiprocessing Process based parallelism Python 3.12[EB/OL]. [2026-10-21]. https://docs.python.org/3.12/library/multiprocessing.html.',
 '[7] Hugging Face. PEFT LoRA configuration[EB/OL]. [2026-10-21]. https://huggingface.co/docs/peft/v0.21.0/package_reference/lora.',
 '[8] Hugging Face. TRL SFT Trainer[EB/OL]. [2026-10-21]. https://huggingface.co/docs/trl/sft_trainer.',
 '[9] Microsoft. Playwright Videos[EB/OL]. [2026-10-21]. https://playwright.dev/docs/videos.',
]


def add_content(anchor, doc, markdown):
    for block in markdown.strip().split('\n\n'):
        if block.startswith('# '): text, style = block[2:], 'Heading 1'
        elif block.startswith('## '): text, style = block[3:], 'Heading 2'
        else: text, style = block, 'Normal'
        p = anchor.insert_paragraph_before(text, style) if anchor else doc.add_paragraph(text, style)
        if style == 'Normal':
            p.paragraph_format.widow_control = True
        elif style == 'Heading 2':
            p.paragraph_format.keep_with_next = True
    return


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    doc = Document(BACKUP)
    original = Document(BACKUP)
    old_head = next(p for p in doc.paragraphs if p.style.name == 'Heading 1' and p.text.startswith('第九章'))
    next_head = next(p for p in doc.paragraphs if p.style.name == 'Heading 1' and p.text.startswith('第十章'))
    node = old_head._p
    while node is not next_head._p:
        following = node.getnext(); node.getparent().remove(node); node = following
    future = (SOURCE/'后续技术方案.md').read_text()
    add_content(next_head, doc, future)
    while doc.paragraphs[-1].text == '' and not doc.paragraphs[-1]._p.xpath('.//w:drawing'):
        el = doc.paragraphs[-1]._p; el.getparent().remove(el)
    doc.add_paragraph('参考文献', 'Heading 1')
    for ref in REFS:
        p = doc.add_paragraph(ref)
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.line_spacing = Pt(18)
        p.paragraph_format.space_after = Pt(6)
    ai = (SOURCE/'生成式AI使用情况说明.md').read_text()
    add_content(None, doc, ai)
    for p in doc.paragraphs:
        if '\t' in p.text and p.text.rsplit('\t', 1)[1].isdigit():
            label = p.text.rsplit('\t', 1)[0]
            if label.startswith('第九章'): label = '第九章 问题讨论与后续技术方案'
            if label.startswith('附录'): label = '附录 生成式AI使用情况说明'
            p.text = label + '\t0'
            p.paragraph_format.tab_stops.add_tab_stop(Cm(15.8), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    for p in doc.paragraphs:
        if p.style.name == 'Heading 1' and p.text != '目录':
            p.paragraph_format.page_break_before = True
        if p.style.name.startswith('Heading'):
            p.paragraph_format.keep_with_next = True
    assert len(doc.tables) == len(original.tables) == 2
    assert len(doc.inline_shapes) == len(original.inline_shapes) == 2
    # Preserve all research content outside the replaced chapter, apart from TOC entries.
    old_text=[p.text for p in original.paragraphs]
    cut9=old_text.index(next(t for t in old_text if t.startswith('第九章') and '\t' not in t))
    cut10=old_text.index('第十章 结论')
    preserved=[p for p in old_text[:cut9]+old_text[cut10:] if p and '\t' not in p]
    new_text=[p.text for p in doc.paragraphs]
    assert all(t in new_text for t in preserved)
    doc.save(TARGET)
    # Export a versioned source matching the revised artifact, including current tables.
    md=[]; in_body=False
    for child in doc.element.body:
        if child.tag == qn('w:p'):
            p=Paragraph(child, doc)
            if p.style.name=='Title': md.append('# '+p.text)
            if p.style.name=='Heading 1' and p.text=='摘要': in_body=True
            if not in_body or not p.text: continue
            if p.style.name=='Heading 1': md.append('# '+p.text)
            elif p.style.name=='Heading 2': md.append('## '+p.text)
            else: md.append(p.text)
        elif in_body and child.tag==qn('w:tbl'):
            table=Table(child,doc)
            rows=[[cell.text.replace('\n',' ') for cell in row.cells] for row in table.rows]
            md.append('\n'.join(['| '+' | '.join(rows[0])+' |','| '+' | '.join(['---']*len(rows[0]))+' |']+
                                ['| '+' | '.join(row)+' |' for row in rows[1:]]))
    (ROOT/'reports/week8/结项报告_20261021修订稿.md').write_text('\n\n'.join(md)+'\n')
    body=[]; in_body=False
    for p in doc.paragraphs:
        if p.style.name=='Heading 1' and p.text.startswith('第一章'): in_body=True
        if p.style.name=='Heading 1' and p.text=='参考文献': break
        if in_body and not p.style.name.startswith('Heading') and not p.text.startswith(('图1','图2','表1','表2')): body.append(p.text)
    stats={'revised_at':'2026-10-21','report':str(TARGET.relative_to(ROOT)),
           'backup_sha256':hashlib.sha256(BACKUP.read_bytes()).hexdigest(),
           'body_chinese_characters':len(re.findall(r'[\u4e00-\u9fff]',''.join(body))),
           'future_work_chinese_characters':len(re.findall(r'[\u4e00-\u9fff]',future)),
           'future_work_subsections':10,'ai_disclosure_at_end':True,
           'preserved_existing_tables':len(doc.tables),'preserved_existing_images':len(doc.inline_shapes),
           'scope':'Documentation revision; proposals not implemented or counted as new experimental results.'}
    (OUT/'report_revision_statistics.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2))
    print(json.dumps(stats,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
