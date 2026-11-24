"""Package current source and declared deliverables without environments or credentials."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/项目源码与结项材料_20261016.zip'


def main():
    files = set()
    for directory, suffixes in [('src',{'.py'}),('tests',{'.py'}),('scripts',{'.py','.mjs'}),
                                ('data/week3',{'.json','.jsonl'}),('reports',{'.md','.txt','.json'})]:
        for p in (ROOT/directory).rglob('*'):
            if p.is_file() and p.suffix in suffixes and '__pycache__' not in p.parts:
                files.add(p)
    for pattern in ('*.md','requirements*.txt','*.command'):
        files.update(ROOT.glob(pattern))
    files.update([ROOT/'gui-agent-console/dist/index.html',ROOT/'gui-agent-console/.openai/hosting.json',ROOT/'gui-agent-console/.gitignore'])
    files.update((ROOT/'output/docx').glob('*.docx'))
    files = {p for p in files if not p.name.startswith('~$')}
    files.update((ROOT/'output/pdf').glob('*.pdf'))
    for folder in ('verification','browser_regression','final_audit'):
        for p in (ROOT/'output/week8'/folder).glob('*'):
            if p.is_file() and p.suffix in {'.json','.log','.gz','.png'}:
                files.add(p)
    for name in ('acceptance_summary.json','document_statistics.json','contents_pages.json','delivery_manifest.json','结项报告_最终正文.md'):
        files.add(ROOT/'output/week8'/name)
    live=ROOT/'output/week8/live_e2e'
    record=json.loads((live/'results.json').read_text())
    files.update([live/'results.json',live/'backend.log'])
    files.update(live.glob('[0-9][0-9]_*.png'))
    for task_id in {c['task_id'] for c in record['cases']}:
        files.update([live/f'task_{task_id}.json',live/f'events_{task_id}.jsonl'])
        files.update((ROOT/'output/local_bridge'/task_id).glob('*'))
    files={p for p in files if p.is_file()}
    with ZipFile(OUT,'w',ZIP_DEFLATED) as archive:
        for p in sorted(files): archive.write(p,p.relative_to(ROOT))
    with ZipFile(OUT) as archive:
        assert archive.testzip() is None
        names=archive.namelist()
        assert 'README.md' in names and 'src/local_bridge.py' in names
        assert not any(any(part in n.split('/') for part in ('.venv','.git','__pycache__','.env')) for n in names)
    summary={'archive':str(OUT.relative_to(ROOT)),'files':len(files),'bytes':OUT.stat().st_size,
             'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),
             'scope':'Current code, public local data, historical reports, final audit and selected controlled test evidence; not a Git repository or fulfillment of missing original-outline requirements.',
             'excluded':'Virtual environment, OCR weights, credentials, Git history, unrelated desktop screenshots and lock files'}
    (ROOT/'output/week8/final_audit/source_package_manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
