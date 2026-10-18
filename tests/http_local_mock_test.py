"""E2E HTTP transport with FAKE Java output. Tests download, not real PlantUML diagrams."""
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as temp:
    d=Path(temp)
    (d/'plantuml.jar').write_text('dummy file; not a real jar')
    script=d/'java'
    script.write_text('#!/bin/sh\ncat >/dev/null\nprintf \'<svg xmlns="http://www.w3.org/2000/svg"><text>mock</text></svg>\'\n')
    script.chmod(0o755)
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    env={**os.environ,'PATH':str(d)+':'+os.environ.get('PATH','/usr/bin:/bin'),'PLANTUML_JAR':str(d/'plantuml.jar')}
    server=subprocess.Popen(['php','-S',f'127.0.0.1:{port}','-t','public','public/router.php'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:urllib.request.urlopen(f'http://127.0.0.1:{port}/api.php?action=status',timeout=.3).close();break
            except Exception:time.sleep(.08)
        else:raise RuntimeError('PHP server did not start')
        payload=json.dumps({'uml':'@startuml\nAlice -> Bob\n@enduml','format':'svg'}).encode()
        def call(action):
            req=urllib.request.Request(f'http://127.0.0.1:{port}/api.php?action={action}',data=payload,headers={'Content-Type':'application/json'},method='POST')
            with urllib.request.urlopen(req,timeout=4) as r:return r.status,r.headers,r.read()
        code,headers,body=call('render')
        parsed=json.loads(body)
        assert code==200 and parsed['mode']=='local' and parsed['format']=='svg' and parsed['base64'], parsed
        code,headers,body=call('download')
        assert code==200
        assert headers['Content-Disposition']=='attachment; filename="diagram.svg"'
        assert headers['Content-Type'].startswith('image/svg+xml')
        assert body.startswith(b'<svg')
        assert headers['Content-Security-Policy']=='sandbox'
        print('PASS mock local render API + attachment headers + bytes (not a real PlantUML image)')
    finally:
        server.terminate();server.wait(timeout=3)
