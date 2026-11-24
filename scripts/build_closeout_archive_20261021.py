"""Archive all standalone reports plus current source and selected evidence, with hashes."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'output/GUI_Agent_结项归档_20261021.zip'
PREFIX = 'GUI_Agent_结项归档_20261021/'
META = ROOT/'output/archive/20261021'
REPORT_SUFFIXES = {'.docx','.pdf','.md','.txt','.xlsx','.pptx'}
CODE_SUFFIXES = {'.py','.mjs','.js','.cjs','.ts','.tsx','.jsx','.html','.css','.json','.sh','.command','.toml','.yaml','.yml','.txt','.md'}


def digest(data): return hashlib.sha256(data).hexdigest()


def main():
    files={}
    def add(p,role):
        if p.is_file() and not p.name.startswith('~$') and not p.is_symlink():
            files[p]=role
    for d in ('src','tests','scripts','gui-agent-console/dist'):
        for p in (ROOT/d).rglob('*'):
            if p.suffix in CODE_SUFFIXES and '__pycache__' not in p.parts:
                add(p,'source')
    for pattern in ('*.md','requirements*.txt','*.command'):
        for p in ROOT.glob(pattern): add(p,'configuration_or_documentation')
    for name in ('.gitignore','gui-agent-console/.gitignore','gui-agent-console/.openai/hosting.json'):
        add(ROOT/name,'configuration')
    for d in ('output/docx','output/pdf','reports'):
        for p in (ROOT/d).rglob('*'):
            if p.suffix in REPORT_SUFFIXES: add(p,'report')
            elif p.suffix=='.json': add(p,'evidence')
    # Include standalone reports preserved inside historical submission folders.
    for p in (ROOT/'output').rglob('*'):
        if any('submission_package' in part for part in p.parts) and p.suffix in REPORT_SUFFIXES:
            add(p,'historical_report')
    for p in (ROOT/'data/week3').rglob('*'):
        if p.suffix in {'.json','.jsonl'}: add(p,'public_data')
    for d in ('output/week3','output/week4','output/week5','output/week6','output/week7','output/week8'):
        for p in (ROOT/d).rglob('*'):
            if p.suffix in {'.json','.jsonl','.log','.txt','.md'}: add(p,'historical_evidence')
    live=ROOT/'output/week8/live_e2e'
    record=json.loads((live/'results.json').read_text())
    for p in live.glob('[0-9][0-9]_*.png'): add(p,'controlled_run_image')
    for p in (ROOT/'output/week8/browser_regression').glob('*.png'): add(p,'browser_test_image')
    for task_id in {c['task_id'] for c in record['cases']}:
        for p in (ROOT/'output/local_bridge'/task_id).glob('*'):
            if p.suffix in {'.png','.json','.jsonl'}: add(p,'controlled_run_evidence')
    add(META/'history/结项报告_修订前.docx','report_history')
    for name in ('report_revision_statistics.json','report_layout.json'):
        add(META/name,'current_revision_metadata')
    # All current official Word and PDF reports must be present exactly once by path.
    official={p for d in ('output/docx','output/pdf') for p in (ROOT/d).rglob('*')
              if p.is_file() and p.suffix in {'.docx','.pdf'} and not p.name.startswith('~$')}
    assert official.issubset(files)
    records=[]
    for p,role in sorted(files.items()):
        raw=p.read_bytes(); rel=p.relative_to(ROOT).as_posix()
        assert not any(part in {'.venv','.git','__pycache__','.env','artifacts'} for part in p.relative_to(ROOT).parts)
        records.append({'path':rel,'category':role,'bytes':len(raw),'sha256':digest(raw)})
    inventory={'archived_at':'2026-10-21','latest_report':'output/docx/结项报告.docx',
               'official_word_reports':sum(p.suffix=='.docx' for p in official),
               'official_pdf_reports':sum(p.suffix=='.pdf' for p in official),
               'source_files':sum(v=='source' for v in files.values()),
               'payload_files':len(records),'files':records,
               'note':'Current reports and source snapshot; historical results keep their original dates. Future work is proposed, not implemented.'}
    inventory_bytes=(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n').encode()
    checksum_bytes=('\n'.join(r['sha256']+'  '+r['path'] for r in records)+'\n').encode()
    with ZipFile(DEST,'w',ZIP_DEFLATED) as z:
        for p in sorted(files): z.write(p,PREFIX+p.relative_to(ROOT).as_posix())
        z.writestr(PREFIX+'归档文件清单.json',inventory_bytes)
        z.writestr(PREFIX+'SHA256SUMS.txt',checksum_bytes)
    with ZipFile(DEST) as z:
        assert z.testzip() is None
        for r in records: assert digest(z.read(PREFIX+r['path']))==r['sha256'],r['path']
        assert len(z.namelist())==len(records)+2
        assert z.read(PREFIX+'output/docx/结项报告.docx')==(ROOT/'output/docx/结项报告.docx').read_bytes()
    META.mkdir(parents=True,exist_ok=True)
    (META/'归档文件清单.json').write_bytes(inventory_bytes)
    (META/'SHA256SUMS.txt').write_bytes(checksum_bytes)
    summary={'archive':str(DEST.relative_to(ROOT)),'bytes':DEST.stat().st_size,
             'sha256':digest(DEST.read_bytes()),'members':len(records)+2,
             'word_reports':inventory['official_word_reports'],'pdf_reports':inventory['official_pdf_reports'],
             'source_files':inventory['source_files'],'all_payload_hashes_verified':True,'zip_crc_verified':True}
    (META/'archive_verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
