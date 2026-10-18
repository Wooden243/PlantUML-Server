"""Offline Chromium DOM/UI smoke test using mocked API and diagram responses.

Not an end-to-end PlantUML rendering test. No local HTTP/network is required.
Requires optional Python `playwright` + Chromium. See README.
"""
import base64
import json
import shutil
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT/'storage/examples.json').read_text())
CSS = (ROOT/'public/assets/style.css').read_text()
JS = (ROOT/'public/assets/app.js').read_text()
SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="390" height="180"><rect width="390" height="180" fill="#fff"/><rect x="22" y="15" width="125" height="33" rx="5" stroke="#587aa2" fill="#e9f2ff"/><rect x="245" y="15" width="125" height="33" rx="5" stroke="#587aa2" fill="#e9f2ff"/><text x="65" y="36" font-size="15">Alice</text><text x="285" y="36" font-size="15">Bob</text><path d="M90 49v100M300 49v100M90 89H300M293 83l7 6-7 6" stroke="#64748b" fill="none"/><text x="160" y="81">hello</text></svg>'
ENCODED = base64.b64encode(SVG.encode()).decode()

def php_html(id=None):
    setup = '$_GET["id"]=' + str(id) + ';' if id else ''
    raw = subprocess.check_output(['php','-r',setup+' include "public/index.php";'],cwd=ROOT)
    return raw.decode().replace('<script defer src="/assets/app.js"></script>','').replace('<link rel="stylesheet" href="/assets/style.css">','')

def mock_window(page,id=None):
    mock_data = json.dumps(DATA,ensure_ascii=False)
    # browser cannot make localhost requests here; serve the real PHP-generated page and stub only API responses
    page.set_content(php_html(id),wait_until='domcontentloaded')
    page.add_style_tag(content=CSS)
    mock = r'''(function(){
        const examples=__EXAMPLES__;
        const b64=__B64__;
        const values=new Map();
        Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)}});
        window.fetch=async function(url,options={}){
          const parsed=new URL(url,'https://example.invalid');
          const action=parsed.searchParams.get('action');
          let result={};let ok=true;
          if(action==='list'){
             const q=parsed.searchParams.get('q')||'';
             const results=examples.filter(x=>x.title.includes(q)||x.theme.includes(q));
             const pages=Math.max(1,Math.ceil(results.length/5));
             const page=Math.min(Math.max(1,Number(parsed.searchParams.get('page')||1)),pages);
             result={items:results.slice((page-1)*5,page*5).map(({id,title,theme})=>({id,title,theme})),page,pages,total:results.length};
          }else if(action==='detail'){
             const id=Number(parsed.searchParams.get('id'));
             result=examples.find(x=>x.id===id)||{};
          }else if(action==='status') result={renderer:'local',hasLocalEngine:true};
          else if(action==='render'){
             const body=JSON.parse(options.body);result={mode:'local',format:body.format,mime:'image/svg+xml',base64:b64};
          }else if(action==='generate') result={uml:'@startuml\\nAlice -> Bob: hello\\n@enduml',generator:'rule-based'};
          return {ok,status:200,json:async()=>result};
        };
    })();'''.replace('__EXAMPLES__',mock_data).replace('__B64__',json.dumps(ENCODED))
    page.evaluate(mock)
    page.add_script_tag(content=JS)

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path=shutil.which('chromium'),args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1365,'height':900},device_scale_factor=1)
    mock_window(page)
    page.wait_for_selector('#diagram-rows tr:nth-child(5)')
    assert page.locator('#diagram-rows tr').count()==5
    page.locator('#search').fill('ライフライン')
    page.wait_for_timeout(360)
    assert page.locator('#diagram-rows tr').count()==1
    page.locator('#search').fill('')
    page.wait_for_timeout(360)
    page.screenshot(path=str(ROOT/'docs/screenshot-library.png'),full_page=True)
    page2=browser.new_page(viewport={'width':1365,'height':900},device_scale_factor=1)
    mock_window(page2,5)
    page2.wait_for_selector('#preview-area img')
    assert 'activate bob' in page2.locator('#uml-input').input_value()
    page2.locator('#show-answer').click()
    assert 'activate bob' in page2.locator('#reference-code').inner_text()
    page2.locator('#prompt-generate').click()
    page2.wait_for_selector('#generated-code:not(.hidden)')
    page2.locator('#apply-generated').click()
    page2.locator('#reset-button').click()
    assert 'activate bob' in page2.locator('#uml-input').input_value()
    page2.screenshot(path=str(ROOT/'docs/screenshot-editor.png'),full_page=True)
    page2.get_by_role('button',name='PNG',exact=True).click()
    page2.wait_for_selector('#preview-area img')
    page2.get_by_role('button',name='ASCII',exact=True).click()
    page2.wait_for_selector('#preview-area pre')
    mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
    mock_window(mobile,5)
    mobile.wait_for_selector('#preview-area img')
    assert mobile.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1')
    mobile.screenshot(path=str(ROOT/'docs/screenshot-mobile.png'),full_page=True)
    browser.close()
print('PASS: Chromium UI controls and responsive layout (mock API & mock rendering; not real network)')
