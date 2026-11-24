"""Render the three deliverables with bundled LibreOffice and explicit CJK fonts."""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path('/Users/ziang/.cache/codex-runtimes/codex-primary-runtime')
PYTHON = RUNTIME / 'dependencies/python/bin/python3'
RENDER = Path('/Users/ziang/.codex/plugins/cache/openai-primary-runtime/documents/26.1013.11914/skills/documents/render_docx.py')


def main():
    directory = ROOT / 'tmp/week8/final'
    directory.mkdir(parents=True, exist_ok=True)
    config = directory / 'fonts.conf'
    fonts = RUNTIME / 'dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fonts/truetype'
    config.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>'
                      '<dir>/System/Library/Fonts/Supplemental</dir>'
                      f'<dir>{fonts}</dir><cachedir>/private/tmp/week8-fontconfig-cache</cachedir></fontconfig>')
    env = {**os.environ, 'FONTCONFIG_FILE': str(config)}
    for filename, folder in [('第八周周报.docx', 'weekly'), ('第八周验收测试报告.docx', 'acceptance'),
                             ('第八周项目结项报告.docx', 'thesis')]:
        subprocess.run([str(PYTHON), str(RENDER), str(ROOT / 'output/docx' / filename),
                        '--output_dir', str(directory / folder), '--emit_pdf', '--dpi', '110'],
                       env=env, check=True)
    subprocess.run([str(PYTHON), 'scripts/finalize_week8_documents.py',
                    str(directory / 'thesis/第八周项目结项报告.pdf')], cwd=ROOT, check=True)
    subprocess.run([str(PYTHON), str(RENDER), str(ROOT / 'output/docx/第八周项目结项报告.docx'),
                    '--output_dir', str(directory / 'thesis'), '--emit_pdf', '--dpi', '110'],
                   env=env, check=True)


if __name__ == '__main__': main()
