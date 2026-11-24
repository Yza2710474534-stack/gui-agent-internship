"""Check the archived snapshot against its recorded SHA-256 manifest."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'archive_manifest.json').read_text(encoding='utf-8'))
bad = []
for record in manifest['files']:
    path = root / record['path']
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
        bad.append(record['path'])
print(f"Checked {len(manifest['files'])} files; mismatches: {len(bad)}")
for path in bad:
    print(path)
raise SystemExit(bool(bad))
