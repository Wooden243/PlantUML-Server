/* PlantUML workspace: no inline HTML injection from UML or user text. */
'use strict';
const $ = (selector) => document.querySelector(selector);
const escapeText = (text) => String(text ?? '');
const request = async (action, payload, method = 'POST') => {
  const response = await fetch('/api.php?action=' + encodeURIComponent(action), {
    method,
    headers: {'Content-Type': 'application/json'},
    body: method === 'POST' ? JSON.stringify(payload) : undefined,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'サーバーに接続できません。');
  return data;
};
const addText = (parent, tag, text, className = '') => {
  const el = document.createElement(tag);
  el.textContent = escapeText(text);
  if (className) el.className = className;
  parent.appendChild(el);
  return el;
};
const setMessage = (container, text, type = 'muted') => {
  container.replaceChildren(addText(document.createDocumentFragment(), 'p', text, type));
};
async function library() {
  const input = $('#search');
  let page = 1;
  let pending;
  const draw = async () => {
    const rows = $('#diagram-rows');
    const pages = $('#pagination');
    rows.replaceChildren();
    pages.replaceChildren();
    try {
      const response = await fetch('/api.php?action=list&page=' + page + '&q=' + encodeURIComponent(input.value));
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || '取得に失敗しました。');
      for (const diagram of data.items) {
        const row = document.createElement('tr');
        addText(row, 'td', diagram.id);
        const title = document.createElement('td');
        const anchor = document.createElement('a');
        anchor.href = '/?id=' + diagram.id;
        anchor.textContent = diagram.title;
        title.appendChild(anchor);
        row.appendChild(title);
        const theme = document.createElement('td');
        addText(theme, 'span', diagram.theme, 'badge');
        row.appendChild(theme);
        const action = document.createElement('td');
        const open = document.createElement('a');
        open.href = '/?id=' + diagram.id;
        open.textContent = '開く →';
        action.appendChild(open);
        row.appendChild(action);
        rows.appendChild(row);
      }
      if (data.items.length === 0) {
        const row = document.createElement('tr');
        const cell = addText(row, 'td', '該当する図がありません。');
        cell.colSpan = 4;
        rows.appendChild(row);
      }
      const makeButton = (text, target, disabled, active = false) => {
        const b = addText(pages, 'button', text);
        b.disabled = disabled;
        if (active) b.className = 'active';
        b.addEventListener('click', () => {page = target; draw();});
      };
      makeButton('‹', data.page - 1, data.page === 1);
      for (let i = 1; i <= data.pages; i++) makeButton(i, i, false, i === data.page);
      makeButton('›', data.page + 1, data.page === data.pages);
    } catch (error) {
      const row = document.createElement('tr');
      const cell = addText(row, 'td', error.message);
      cell.colSpan = 4;
      rows.appendChild(row);
    }
  };
  input.addEventListener('input', () => {clearTimeout(pending);pending = setTimeout(() => {page = 1;draw();}, 220);});
  draw();
}
function toDataURL(mime, base64) { return 'data:' + mime + ';base64,' + base64; }
async function initializeDetail(id) {
  // Detail lookup uses the URL id so direct navigation is supported.
  const response = await fetch('/api.php?action=detail&id=' + encodeURIComponent(id));
  if (!response.ok) throw new Error('図を取得できませんでした。');
  const item = await response.json();
  const textarea = $('#uml-input');
  const storageKey = 'plantuml-exercise-' + id;
  const saved = localStorage.getItem(storageKey);
  textarea.value = saved === null ? item.uml : saved;
  const example = item.uml;
  let currentFormat = 'svg';
  let lastResult = null;
  let currentRequest = 0;
  let currentTimer;
  let editor = null;
  let pendingGenerated = '';
  $('#description').value = item.prompt;
  const getValue = () => editor ? editor.getValue() : textarea.value;
  const setValue = (text) => {
    if (editor) editor.setValue(text);
    else {textarea.value = text; textarea.dispatchEvent(new Event('input'));}
  };
  let engineLocal = false;
  try {
    const status = await request('status', null, 'GET');
    engineLocal = status.hasLocalEngine;
    $('#engine-state').textContent = engineLocal ? 'ローカルPlantUML' : '公式サーバー利用';
    $('#privacy-note').textContent = engineLocal ? 'この環境では、図のレンダリングはローカルのJARで実行します。' : 'PlantUML JAR未設置のため、図のソースが公式PlantUMLサーバーへ送信されます。機密情報は入力しないでください。';
  } catch (error) { $('#engine-state').textContent = 'エンジン未確認'; }
  const display = (data, format) => {
    const box = $('#preview-area');
    box.replaceChildren();
    if (data.mode === 'remote') {
      if (format === 'txt') {
        const frame = document.createElement('iframe');
        frame.title = 'PlantUML ASCII preview';
        frame.sandbox = '';
        frame.src = data.url;
        box.appendChild(frame);
      } else {
        const image = document.createElement('img');
        image.alt = 'PlantUML ' + format + ' diagram';
        image.src = data.url;
        image.addEventListener('error', () => setMessage(box, '外部PlantUMLサーバーへ接続できません。JARのローカル導入を推奨します。', 'error'), {once:true});
        box.appendChild(image);
      }
    } else if (format === 'txt') {
      const pre = document.createElement('pre');
      const asciiBytes = Uint8Array.from(atob(data.base64), char => char.charCodeAt(0));
      pre.textContent = new TextDecoder('utf-8').decode(asciiBytes);
      box.appendChild(pre);
    } else {
      const image = document.createElement('img');
      image.alt = 'PlantUML ' + format + ' diagram';
      image.src = toDataURL(data.mime, data.base64);
      box.appendChild(image);
    }
  };
  const render = async () => {
    const thisRequest = ++currentRequest;
    const code = getValue();
    $('#render-status').textContent = '描画中...';
    try {
      const result = await request('render', {uml:code,format:currentFormat});
      if (thisRequest !== currentRequest) return;
      lastResult = result;
      display(result, currentFormat);
      $('#render-status').textContent = result.mode === 'local' ? 'ローカルで描画しました' : 'PlantUML公式サーバーで表示';
    } catch(error) {
      if (thisRequest !== currentRequest) return;
      lastResult = null;
      setMessage($('#preview-area'), error.message, 'error');
      $('#render-status').textContent = '描画できませんでした';
    }
  };
  const onEdit = () => {
    localStorage.setItem(storageKey, getValue());
    $('#editor-state').textContent = 'ローカルに自動保存済み';
    clearTimeout(currentTimer);
    currentTimer = setTimeout(render, 650);
  };
  textarea.addEventListener('input', onEdit);
  $('#render-button').addEventListener('click', render);
  $('#reset-button').addEventListener('click', () => {setValue(example);localStorage.removeItem(storageKey);render();});
  for (const button of document.querySelectorAll('[data-format]')) {
    button.addEventListener('click', () => {
      document.querySelectorAll('[data-format]').forEach(x => x.classList.toggle('active', x === button));
      currentFormat = button.dataset.format;
      render();
    });
  }
  $('#download-button').addEventListener('click', async () => {
    const button = $('#download-button');
    button.disabled = true;
    try {
      if (engineLocal) {
        const response = await fetch('/api.php?action=download', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({uml:getValue(),format:currentFormat})});
        if (!response.ok) {const data=await response.json(); throw new Error(data.error || 'ダウンロード失敗');}
        const blob = await response.blob();
        const objectURL = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = objectURL;
        anchor.download = 'diagram.' + currentFormat;
        document.body.appendChild(anchor);
        anchor.click();anchor.remove();
        setTimeout(() => URL.revokeObjectURL(objectURL),1000);
      } else {
        const url = lastResult?.format === currentFormat && lastResult?.mode === 'remote' ? lastResult.url : null;
        if (!url) throw new Error('まず図をプレビューしてください。');
        window.open(url, '_blank', 'noopener,noreferrer');
        $('#render-status').textContent = '新しいタブから「名前を付けて保存」してください。';
      }
    } catch(error){ $('#render-status').textContent = error.message; }
    finally {button.disabled=false;}
  });
  $('#show-answer').addEventListener('click', () => {
    $('#answerbox').classList.toggle('hidden');
    $('#current-code').textContent = getValue();
    $('#reference-code').textContent = example;
    $('#show-answer').textContent = $('#answerbox').classList.contains('hidden') ? '模範解答を表示' : '模範解答を隠す';
  });
  $('#copy-answer').addEventListener('click', async () => {
    try {await navigator.clipboard.writeText(example);$('#copy-answer').textContent = 'コピーしました';}
    catch {$('#copy-answer').textContent = 'コピーできませんでした';}
  });
  $('#prompt-generate').addEventListener('click', async () => {
    $('#generated-code').classList.remove('hidden');
    try {
      const generated = await request('generate', {description:$('#description').value,theme:item.theme});
      pendingGenerated = generated.uml;
      $('#generated-code').textContent = pendingGenerated;
      $('#apply-generated').disabled = false;
    } catch(error) {$('#generated-code').textContent = error.message;}
  });
  $('#apply-generated').addEventListener('click', () => {if (pendingGenerated) {setValue(pendingGenerated);onEdit();render();}});
  render();
  // Monaco is optional. Fallback textarea remains usable offline.
  const loader = document.createElement('script');
  loader.src = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs/loader.min.js';
  loader.onload = () => {
    if (typeof window.require !== 'function') return;
    window.require.config({paths:{vs:'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs'}});
    window.require(['vs/editor/editor.main'], () => {
      const container = $('#monaco-container');
      if (!container) return;
      const code = textarea.value;
      textarea.style.display = 'none';
      const host = document.createElement('div');
      host.style.cssText = 'position:absolute;inset:0';
      container.appendChild(host);
      editor = window.monaco.editor.create(host,{value:code,language:'plaintext',theme:'vs',fontSize:13,minimap:{enabled:false},automaticLayout:true,wordWrap:'on'});
      editor.onDidChangeModelContent(onEdit);
      $('#editor-state').textContent = 'Monaco Editor';
    }, () => {});
  };
  loader.onerror = () => { $('#editor-state').textContent = '標準エディタ（オフライン）'; };
  document.head.appendChild(loader);
}
(async()=>{
  try {
    const id = document.body.dataset.id;
    if (id) await initializeDetail(id);
    else await library();
  } catch(error) {
    const area = $('#preview-area');
    if (area) setMessage(area, error.message, 'error');
  }
})();
