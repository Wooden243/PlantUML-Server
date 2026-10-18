#!/usr/bin/env python3
"""Build deterministic-ish submission ZIP with only required files."""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT.parent/(ROOT.name+'.zip')
exclude_dirs={'.git','__pycache__','.venv','.idea','.vscode'}
excluded_ext={'.pyc','.log','.jar'}
files=[]
for path in ROOT.rglob('*'):
    if not path.is_file():continue
    if any(x in exclude_dirs for x in path.relative_to(ROOT).parts):continue
    if path.suffix in excluded_ext:continue
    if path.name=='.env':continue
    files.append(path)
with zipfile.ZipFile(TARGET,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as zipf:
    for path in sorted(files):
        zipf.write(path,arcname=str(Path(ROOT.name)/path.relative_to(ROOT)))
with zipfile.ZipFile(TARGET) as zipf:
    bad=zipf.testzip()
    assert bad is None,bad
    assert all(not n.endswith('.jar') for n in zipf.namelist())
    print('ZIP:',TARGET,'files:',len(zipf.namelist()),'bytes:',TARGET.stat().st_size)
