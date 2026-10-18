"""Real HTTP checks against PHP's built-in server; stdlib only."""
import json
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
import unittest

PROJECT = Path(__file__).resolve().parents[1]

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]

class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = free_port()
        cls.base = f'http://127.0.0.1:{cls.port}'
        cls.server = subprocess.Popen(['php', '-S', f'127.0.0.1:{cls.port}', '-t', 'public', 'public/router.php'], cwd=PROJECT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(80):
            try:
                urllib.request.urlopen(cls.base + '/', timeout=.3).close()
                return
            except Exception:
                if cls.server.poll() is not None:
                    raise RuntimeError('PHP server failed to start')
                time.sleep(.075)
        raise RuntimeError('PHP server did not start')

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        try:cls.server.wait(timeout=2)
        except subprocess.TimeoutExpired:cls.server.kill()

    def fetch(self, path, payload=None, method=None):
        data = None if payload is None else json.dumps(payload).encode('utf-8')
        headers = {'Content-Type':'application/json'} if data is not None else {}
        req = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=4) as response:
                content = response.read()
                return response.status, dict(response.headers), content
        except urllib.error.HTTPError as error:
            return error.code, dict(error.headers), error.read()

    def test_homepage(self):
        status, headers, data = self.fetch('/')
        self.assertEqual(status,200)
        self.assertIn(b'PlantUML Server',data)
        self.assertIn(b'diagram-rows',data)

    def test_detailpage(self):
        status, _, data = self.fetch('/?id=5')
        self.assertEqual(status,200)
        self.assertIn(b'uml-input',data)
        self.assertIn(b'engine-state',data)

    def test_missing_page_404(self):
        status,_,_=self.fetch('/?id=99999')
        self.assertEqual(status,404)

    def test_static_js(self):
        status,headers,data = self.fetch('/assets/app.js')
        self.assertEqual(status,200)
        self.assertIn(b'Monaco',data)

    def test_list_pagination(self):
        status,_,data=self.fetch('/api.php?action=list&page=3')
        obj=json.loads(data)
        self.assertEqual((status,obj['page'],obj['total'],len(obj['items'])),(200,3,20,5))
        self.assertNotIn('uml',obj['items'][0])

    def test_list_search(self):
        status,_,data=self.fetch('/api.php?action=list&q=%E3%83%A9%E3%82%A4%E3%83%95%E3%83%A9%E3%82%A4%E3%83%B3')
        self.assertEqual(status,200)
        self.assertEqual(json.loads(data)['total'],1)

    def test_detail_source(self):
        status,_,data=self.fetch('/api.php?action=detail&id=5')
        obj=json.loads(data)
        self.assertEqual(status,200)
        self.assertIn('activate',obj['uml'])

    def test_detail_invalid(self):
        status,_,_=self.fetch('/api.php?action=detail&id=bad')
        self.assertEqual(status,422)

    def test_detail_notfound(self):
        status,_,_=self.fetch('/api.php?action=detail&id=9999')
        self.assertEqual(status,404)

    def test_status(self):
        status,_,data=self.fetch('/api.php?action=status')
        obj=json.loads(data)
        self.assertEqual(status,200)
        self.assertIn(obj['renderer'],['local','remote'])

    def test_remote_render_svg(self):
        status,_,data=self.fetch('/api.php?action=render',{'uml':'@startuml\nAlice -> Bob: hi\n@enduml','format':'svg'})
        obj=json.loads(data)
        self.assertEqual(status,200)
        self.assertIn(obj['mode'], ['local','remote'])
        if obj['mode']=='remote':self.assertTrue(obj['url'].startswith('https://www.plantuml.com/plantuml/svg/'))

    def test_remote_render_png(self):
        status,_,data=self.fetch('/api.php?action=render',{'uml':'@startuml\nAlice -> Bob: hi\n@enduml','format':'png'})
        self.assertEqual(status,200)
        self.assertEqual(json.loads(data)['format'],'png')

    def test_remote_render_ascii(self):
        status,_,data=self.fetch('/api.php?action=render',{'uml':'@startuml\nAlice -> Bob: hi\n@enduml','format':'txt'})
        self.assertEqual(status,200)
        self.assertEqual(json.loads(data)['format'],'txt')

    def test_invalid_format(self):
        status,_,_=self.fetch('/api.php?action=render',{'uml':'abc','format':'exe'})
        self.assertEqual(status,422)

    def test_invalid_source(self):
        status,_,_=self.fetch('/api.php?action=render',{'uml':'','format':'svg'})
        self.assertEqual(status,422)

    def test_include_blocked(self):
        status,_,_=self.fetch('/api.php?action=render',{'uml':'!include https://evil.example/test','format':'svg'})
        self.assertEqual(status,422)

    def test_large_source(self):
        status,_,_=self.fetch('/api.php?action=render',{'uml':'a'*15000,'format':'svg'})
        self.assertEqual(status,422)

    def test_bad_json(self):
        req=urllib.request.Request(self.base+'/api.php?action=render',data=b'{broken',headers={'Content-Type':'application/json'})
        with self.assertRaises(urllib.error.HTTPError) as exc:urllib.request.urlopen(req,timeout=4)
        self.assertEqual(exc.exception.code,422)

    def test_generate(self):
        status,_,data=self.fetch('/api.php?action=generate',{'description':'Alice -> Bob: Hi','theme':'シーケンス図'})
        self.assertEqual(status,200)
        self.assertIn('Alice -> Bob: Hi',json.loads(data)['uml'])
        self.assertEqual(json.loads(data)['generator'],'rule-based')

    def test_generate_error(self):
        status,_,_=self.fetch('/api.php?action=generate',{'description':''})
        self.assertEqual(status,422)

    def test_download_missing_jar(self):
        status,headers,data=self.fetch('/api.php?action=download',{'uml':'@startuml\nA -> B\n@enduml','format':'svg'})
        self.assertIn(status,[200,503])
        if status==503:self.assertIn('url',json.loads(data))

    def test_no_files_outside_public(self):
        for path in ['/storage/examples.json','/src/Renderer.php','/.gitignore']:
            status,_,data=self.fetch(path)
            self.assertNotEqual(status,200, path)
            self.assertNotIn(b'"prompt"',data)

    def test_post_list_disallowed(self):
        status,_,_=self.fetch('/api.php?action=list',{'anything':'anything'})
        self.assertEqual(status,404)

    def test_unsupported_get(self):
        status,_,_=self.fetch('/api.php?action=none')
        self.assertEqual(status,404)

    def test_http_security_headers(self):
        status,headers,_=self.fetch('/api.php?action=status')
        self.assertEqual(status,200)
        self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
        self.assertEqual(headers['Referrer-Policy'],'no-referrer')

if __name__=='__main__':unittest.main(verbosity=2)
