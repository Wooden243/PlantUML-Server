#!/usr/bin/env python3
"""Checks exact source SHA-256 and exact fenced code in each walkthrough."""
from pathlib import Path
import hashlib
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
directory=ROOT/'learning/code-walkthrough'
passed=0
for file in sorted(directory.glob('*.md')):
    if file.stem=='README':continue
    content=file.read_text()
    match=re.search(r'^対象：`([^`]+)`$',content,re.M)
    digest=re.search(r'^ソースSHA-256：`([0-9a-f]{64})`$',content,re.M)
    if not match or not digest:raise AssertionError(file.name+' missing metadata')
    target=ROOT/match.group(1)
    source=target.read_text()
    suffix='js' if target.suffix=='.js' else 'php'
    start=content.index('```'+suffix+'\n')+len('```'+suffix+'\n')
    end=content.index('\n```',start)
    captured=content[start:end]+'\n'
    assert captured == source,file.name+' source differs'
    assert hashlib.sha256(source.encode()).hexdigest()==digest.group(1),file.name+' hash differs'
    print('PASS',file.name, target.relative_to(ROOT))
    passed+=1
print('PASS: all',passed,'walkthroughs match source')
sys.exit(0)
