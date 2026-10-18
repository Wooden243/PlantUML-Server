# app.js — ソースコード全文と逐次解説

対象：`public/assets/app.js`
ソースSHA-256：`8c34af4388f94074c53a1b46a8c286390dff92406348813a4d8046655d88214b`

## 1. 役割と関連ファイル

ブラウザUIの状態・イベント・非同期API通信・画像表示・自動保存を担う。

**前提知識**：DOM、`fetch`、Promise、`async/await`、`localStorage`、`Blob`と`ObjectURL`。

**実行例**：テキストを編集→650ms待つ→POST描画→形式に応じて`img`または`pre/iframe`へ表示する。

## 2. ソースコード全文（省略なし）

```js
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
```

以下では実際のソースの上から下へ進み、原文を小さな範囲に分けて説明する。

## 3. 行・ブロック単位の逐次解説

### 1〜9行

```js
/* PlantUML workspace: no inline HTML injection from UML or user text. */
'use strict';
const $ = (selector) => document.querySelector(selector);
const escapeText = (text) => String(text ?? '');
const request = async (action, payload, method = 'POST') => {
  const response = await fetch('/api.php?action=' + encodeURIComponent(action), {
    method,
    headers: {'Content-Type': 'application/json'},
    body: method === 'POST' ? JSON.stringify(payload) : undefined,
```

- **1行目** `/* PlantUML workspace: no inline HTML injection from UML or user text. */`：コメント。処理意図・注意事項を記し、実行結果には直接影響しない。
- **2行目** `'use strict';`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **3行目** `const $ = (selector) => document.querySelector(selector);`：CSSセレクタを使ってHTMLの特定要素を取得する。
- **4行目** `const escapeText = (text) => String(text ?? '');`：定数を定義する。変化しない上限・設定値として使う。
- **5行目** `const request = async (action, payload, method = 'POST') => {`：定数を定義する。変化しない上限・設定値として使う。
- **6行目** `const response = await fetch('/api.php?action=' + encodeURIComponent(action), {`：定数を定義する。変化しない上限・設定値として使う。
- **7行目** `method,`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **8行目** `headers: {'Content-Type': 'application/json'},`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **9行目** `body: method === 'POST' ? JSON.stringify(payload) : undefined,`：JavaScriptオブジェクトをHTTPで送れるJSON文字列へ変換する。

### 10〜18行

```js
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'サーバーに接続できません。');
  return data;
};
const addText = (parent, tag, text, className = '') => {
  const el = document.createElement(tag);
  el.textContent = escapeText(text);
  if (className) el.className = className;
```

- **11行目** `const data = await response.json();`：定数を定義する。変化しない上限・設定値として使う。
- **12行目** `if (!response.ok) throw new Error(data.error || 'サーバーに接続できません。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **13行目** `return data;`：関数の処理を終了し、呼出元に値を返す。
- **15行目** `const addText = (parent, tag, text, className = '') => {`：定数を定義する。変化しない上限・設定値として使う。
- **16行目** `const el = document.createElement(tag);`：定数を定義する。変化しない上限・設定値として使う。
- **17行目** `el.textContent = escapeText(text);`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **18行目** `if (className) el.className = className;`：条件分岐。条件が真の場合にだけ対応する処理を実行する。

### 19〜27行

```js
  parent.appendChild(el);
  return el;
};
const setMessage = (container, text, type = 'muted') => {
  container.replaceChildren(addText(document.createDocumentFragment(), 'p', text, type));
};
async function library() {
  const input = $('#search');
  let page = 1;
```

- **19行目** `parent.appendChild(el);`：DOMツリーに新しい要素を追加する。
- **20行目** `return el;`：関数の処理を終了し、呼出元に値を返す。
- **22行目** `const setMessage = (container, text, type = 'muted') => {`：定数を定義する。変化しない上限・設定値として使う。
- **23行目** `container.replaceChildren(addText(document.createDocumentFragment(), 'p', text, type));`：既存のDOM内容を消し、最新の要素へ置き換える。
- **25行目** `async function library() {`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。
- **26行目** `const input = $('#search');`：定数を定義する。変化しない上限・設定値として使う。
- **27行目** `let page = 1;`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。

### 28〜36行

```js
  let pending;
  const draw = async () => {
    const rows = $('#diagram-rows');
    const pages = $('#pagination');
    rows.replaceChildren();
    pages.replaceChildren();
    try {
      const response = await fetch('/api.php?action=list&page=' + page + '&q=' + encodeURIComponent(input.value));
      const data = await response.json();
```

- **28行目** `let pending;`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **29行目** `const draw = async () => {`：定数を定義する。変化しない上限・設定値として使う。
- **30行目** `const rows = $('#diagram-rows');`：定数を定義する。変化しない上限・設定値として使う。
- **31行目** `const pages = $('#pagination');`：定数を定義する。変化しない上限・設定値として使う。
- **32行目** `rows.replaceChildren();`：既存のDOM内容を消し、最新の要素へ置き換える。
- **33行目** `pages.replaceChildren();`：既存のDOM内容を消し、最新の要素へ置き換える。
- **34行目** `try {`：失敗する可能性のある処理を開始し、失敗時はcatchへ制御が移る。
- **35行目** `const response = await fetch('/api.php?action=list&page=' + page + '&q=' + encodeURICom…`：定数を定義する。変化しない上限・設定値として使う。
- **36行目** `const data = await response.json();`：定数を定義する。変化しない上限・設定値として使う。

### 37〜45行

```js
      if (!response.ok) throw new Error(data.error || '取得に失敗しました。');
      for (const diagram of data.items) {
        const row = document.createElement('tr');
        addText(row, 'td', diagram.id);
        const title = document.createElement('td');
        const anchor = document.createElement('a');
        anchor.href = '/?id=' + diagram.id;
        anchor.textContent = diagram.title;
        title.appendChild(anchor);
```

- **37行目** `if (!response.ok) throw new Error(data.error || '取得に失敗しました。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **38行目** `for (const diagram of data.items) {`：定数を定義する。変化しない上限・設定値として使う。
- **39行目** `const row = document.createElement('tr');`：定数を定義する。変化しない上限・設定値として使う。
- **40行目** `addText(row, 'td', diagram.id);`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **41行目** `const title = document.createElement('td');`：定数を定義する。変化しない上限・設定値として使う。
- **42行目** `const anchor = document.createElement('a');`：定数を定義する。変化しない上限・設定値として使う。
- **43行目** `anchor.href = '/?id=' + diagram.id;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **44行目** `anchor.textContent = diagram.title;`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **45行目** `title.appendChild(anchor);`：DOMツリーに新しい要素を追加する。

### 46〜54行

```js
        row.appendChild(title);
        const theme = document.createElement('td');
        addText(theme, 'span', diagram.theme, 'badge');
        row.appendChild(theme);
        const action = document.createElement('td');
        const open = document.createElement('a');
        open.href = '/?id=' + diagram.id;
        open.textContent = '開く →';
        action.appendChild(open);
```

- **46行目** `row.appendChild(title);`：DOMツリーに新しい要素を追加する。
- **47行目** `const theme = document.createElement('td');`：定数を定義する。変化しない上限・設定値として使う。
- **48行目** `addText(theme, 'span', diagram.theme, 'badge');`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **49行目** `row.appendChild(theme);`：DOMツリーに新しい要素を追加する。
- **50行目** `const action = document.createElement('td');`：定数を定義する。変化しない上限・設定値として使う。
- **51行目** `const open = document.createElement('a');`：定数を定義する。変化しない上限・設定値として使う。
- **52行目** `open.href = '/?id=' + diagram.id;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **53行目** `open.textContent = '開く →';`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **54行目** `action.appendChild(open);`：DOMツリーに新しい要素を追加する。

### 55〜63行

```js
        row.appendChild(action);
        rows.appendChild(row);
      }
      if (data.items.length === 0) {
        const row = document.createElement('tr');
        const cell = addText(row, 'td', '該当する図がありません。');
        cell.colSpan = 4;
        rows.appendChild(row);
      }
```

- **55行目** `row.appendChild(action);`：DOMツリーに新しい要素を追加する。
- **56行目** `rows.appendChild(row);`：DOMツリーに新しい要素を追加する。
- **58行目** `if (data.items.length === 0) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **59行目** `const row = document.createElement('tr');`：定数を定義する。変化しない上限・設定値として使う。
- **60行目** `const cell = addText(row, 'td', '該当する図がありません。');`：定数を定義する。変化しない上限・設定値として使う。
- **61行目** `cell.colSpan = 4;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **62行目** `rows.appendChild(row);`：DOMツリーに新しい要素を追加する。

### 64〜72行

```js
      const makeButton = (text, target, disabled, active = false) => {
        const b = addText(pages, 'button', text);
        b.disabled = disabled;
        if (active) b.className = 'active';
        b.addEventListener('click', () => {page = target; draw();});
      };
      makeButton('‹', data.page - 1, data.page === 1);
      for (let i = 1; i <= data.pages; i++) makeButton(i, i, false, i === data.page);
      makeButton('›', data.page + 1, data.page === data.pages);
```

- **64行目** `const makeButton = (text, target, disabled, active = false) => {`：定数を定義する。変化しない上限・設定値として使う。
- **65行目** `const b = addText(pages, 'button', text);`：定数を定義する。変化しない上限・設定値として使う。
- **66行目** `b.disabled = disabled;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **67行目** `if (active) b.className = 'active';`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **68行目** `b.addEventListener('click', () => {page = target; draw();});`：クリックや入力変更などのブラウザイベントにコールバックを登録する。
- **70行目** `makeButton('‹', data.page - 1, data.page === 1);`：値または属性を設定する。変数と代入される値の種類を確認する。
- **71行目** `for (let i = 1; i <= data.pages; i++) makeButton(i, i, false, i === data.page);`：繰り返し処理。終了条件とインクリメントを必ず確認する。
- **72行目** `makeButton('›', data.page + 1, data.page === data.pages);`：値または属性を設定する。変数と代入される値の種類を確認する。

### 73〜81行

```js
    } catch (error) {
      const row = document.createElement('tr');
      const cell = addText(row, 'td', error.message);
      cell.colSpan = 4;
      rows.appendChild(row);
    }
  };
  input.addEventListener('input', () => {clearTimeout(pending);pending = setTimeout(() => {page = 1;draw();}, 220);});
  draw();
```

- **73行目** `} catch (error) {`：先行処理が投げた例外を受け、ユーザーに表示するエラーへ変換する。
- **74行目** `const row = document.createElement('tr');`：定数を定義する。変化しない上限・設定値として使う。
- **75行目** `const cell = addText(row, 'td', error.message);`：定数を定義する。変化しない上限・設定値として使う。
- **76行目** `cell.colSpan = 4;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **77行目** `rows.appendChild(row);`：DOMツリーに新しい要素を追加する。
- **80行目** `input.addEventListener('input', () => {clearTimeout(pending);pending = setTimeout(() =>…`：クリックや入力変更などのブラウザイベントにコールバックを登録する。
- **81行目** `draw();`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。

### 82〜90行

```js
}
function toDataURL(mime, base64) { return 'data:' + mime + ';base64,' + base64; }
async function initializeDetail(id) {
  // Detail lookup uses the URL id so direct navigation is supported.
  const response = await fetch('/api.php?action=detail&id=' + encodeURIComponent(id));
  if (!response.ok) throw new Error('図を取得できませんでした。');
  const item = await response.json();
  const textarea = $('#uml-input');
  const storageKey = 'plantuml-exercise-' + id;
```

- **83行目** `function toDataURL(mime, base64) { return 'data:' + mime + ';base64,' + base64; }`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。
- **84行目** `async function initializeDetail(id) {`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。
- **85行目** `// Detail lookup uses the URL id so direct navigation is supported.`：コメント。処理意図・注意事項を記し、実行結果には直接影響しない。
- **86行目** `const response = await fetch('/api.php?action=detail&id=' + encodeURIComponent(id));`：定数を定義する。変化しない上限・設定値として使う。
- **87行目** `if (!response.ok) throw new Error('図を取得できませんでした。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **88行目** `const item = await response.json();`：定数を定義する。変化しない上限・設定値として使う。
- **89行目** `const textarea = $('#uml-input');`：定数を定義する。変化しない上限・設定値として使う。
- **90行目** `const storageKey = 'plantuml-exercise-' + id;`：定数を定義する。変化しない上限・設定値として使う。

### 91〜99行

```js
  const saved = localStorage.getItem(storageKey);
  textarea.value = saved === null ? item.uml : saved;
  const example = item.uml;
  let currentFormat = 'svg';
  let lastResult = null;
  let currentRequest = 0;
  let currentTimer;
  let editor = null;
  let pendingGenerated = '';
```

- **91行目** `const saved = localStorage.getItem(storageKey);`：定数を定義する。変化しない上限・設定値として使う。
- **92行目** `textarea.value = saved === null ? item.uml : saved;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **93行目** `const example = item.uml;`：定数を定義する。変化しない上限・設定値として使う。
- **94行目** `let currentFormat = 'svg';`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **95行目** `let lastResult = null;`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **96行目** `let currentRequest = 0;`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **97行目** `let currentTimer;`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **98行目** `let editor = null;`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **99行目** `let pendingGenerated = '';`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。

### 100〜108行

```js
  $('#description').value = item.prompt;
  const getValue = () => editor ? editor.getValue() : textarea.value;
  const setValue = (text) => {
    if (editor) editor.setValue(text);
    else {textarea.value = text; textarea.dispatchEvent(new Event('input'));}
  };
  let engineLocal = false;
  try {
    const status = await request('status', null, 'GET');
```

- **100行目** `$('#description').value = item.prompt;`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **101行目** `const getValue = () => editor ? editor.getValue() : textarea.value;`：定数を定義する。変化しない上限・設定値として使う。
- **102行目** `const setValue = (text) => {`：定数を定義する。変化しない上限・設定値として使う。
- **103行目** `if (editor) editor.setValue(text);`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **104行目** `else {textarea.value = text; textarea.dispatchEvent(new Event('input'));}`：先の条件が満たされなかったときの分岐。
- **106行目** `let engineLocal = false;`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **107行目** `try {`：失敗する可能性のある処理を開始し、失敗時はcatchへ制御が移る。
- **108行目** `const status = await request('status', null, 'GET');`：定数を定義する。変化しない上限・設定値として使う。

### 109〜117行

```js
    engineLocal = status.hasLocalEngine;
    $('#engine-state').textContent = engineLocal ? 'ローカルPlantUML' : '公式サーバー利用';
    $('#privacy-note').textContent = engineLocal ? 'この環境では、図のレンダリングはローカルのJARで実行します。' : 'PlantUML JAR未設置のため、図のソースが公式PlantUMLサーバーへ送信されます。機密情報は入力しないでください。';
  } catch (error) { $('#engine-state').textContent = 'エンジン未確認'; }
  const display = (data, format) => {
    const box = $('#preview-area');
    box.replaceChildren();
    if (data.mode === 'remote') {
      if (format === 'txt') {
```

- **109行目** `engineLocal = status.hasLocalEngine;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **110行目** `$('#engine-state').textContent = engineLocal ? 'ローカルPlantUML' : '公式サーバー利用';`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **111行目** `$('#privacy-note').textContent = engineLocal ? 'この環境では、図のレンダリングはローカルのJARで実行します。' : 'Pla…`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **112行目** `} catch (error) { $('#engine-state').textContent = 'エンジン未確認'; }`：先行処理が投げた例外を受け、ユーザーに表示するエラーへ変換する。
- **113行目** `const display = (data, format) => {`：定数を定義する。変化しない上限・設定値として使う。
- **114行目** `const box = $('#preview-area');`：定数を定義する。変化しない上限・設定値として使う。
- **115行目** `box.replaceChildren();`：既存のDOM内容を消し、最新の要素へ置き換える。
- **116行目** `if (data.mode === 'remote') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **117行目** `if (format === 'txt') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。

### 118〜126行

```js
        const frame = document.createElement('iframe');
        frame.title = 'PlantUML ASCII preview';
        frame.sandbox = '';
        frame.src = data.url;
        box.appendChild(frame);
      } else {
        const image = document.createElement('img');
        image.alt = 'PlantUML ' + format + ' diagram';
        image.src = data.url;
```

- **118行目** `const frame = document.createElement('iframe');`：定数を定義する。変化しない上限・設定値として使う。
- **119行目** `frame.title = 'PlantUML ASCII preview';`：値または属性を設定する。変数と代入される値の種類を確認する。
- **120行目** `frame.sandbox = '';`：値または属性を設定する。変数と代入される値の種類を確認する。
- **121行目** `frame.src = data.url;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **122行目** `box.appendChild(frame);`：DOMツリーに新しい要素を追加する。
- **123行目** `} else {`：先の条件が満たされなかったときの分岐。
- **124行目** `const image = document.createElement('img');`：定数を定義する。変化しない上限・設定値として使う。
- **125行目** `image.alt = 'PlantUML ' + format + ' diagram';`：値または属性を設定する。変数と代入される値の種類を確認する。
- **126行目** `image.src = data.url;`：値または属性を設定する。変数と代入される値の種類を確認する。

### 127〜135行

```js
        image.addEventListener('error', () => setMessage(box, '外部PlantUMLサーバーへ接続できません。JARのローカル導入を推奨します。', 'error'), {once:true});
        box.appendChild(image);
      }
    } else if (format === 'txt') {
      const pre = document.createElement('pre');
      const asciiBytes = Uint8Array.from(atob(data.base64), char => char.charCodeAt(0));
      pre.textContent = new TextDecoder('utf-8').decode(asciiBytes);
      box.appendChild(pre);
    } else {
```

- **127行目** `image.addEventListener('error', () => setMessage(box, '外部PlantUMLサーバーへ接続できません。JARのローカル導…`：クリックや入力変更などのブラウザイベントにコールバックを登録する。
- **128行目** `box.appendChild(image);`：DOMツリーに新しい要素を追加する。
- **130行目** `} else if (format === 'txt') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **131行目** `const pre = document.createElement('pre');`：定数を定義する。変化しない上限・設定値として使う。
- **132行目** `const asciiBytes = Uint8Array.from(atob(data.base64), char => char.charCodeAt(0));`：定数を定義する。変化しない上限・設定値として使う。
- **133行目** `pre.textContent = new TextDecoder('utf-8').decode(asciiBytes);`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **134行目** `box.appendChild(pre);`：DOMツリーに新しい要素を追加する。
- **135行目** `} else {`：先の条件が満たされなかったときの分岐。

### 136〜144行

```js
      const image = document.createElement('img');
      image.alt = 'PlantUML ' + format + ' diagram';
      image.src = toDataURL(data.mime, data.base64);
      box.appendChild(image);
    }
  };
  const render = async () => {
    const thisRequest = ++currentRequest;
    const code = getValue();
```

- **136行目** `const image = document.createElement('img');`：定数を定義する。変化しない上限・設定値として使う。
- **137行目** `image.alt = 'PlantUML ' + format + ' diagram';`：値または属性を設定する。変数と代入される値の種類を確認する。
- **138行目** `image.src = toDataURL(data.mime, data.base64);`：値または属性を設定する。変数と代入される値の種類を確認する。
- **139行目** `box.appendChild(image);`：DOMツリーに新しい要素を追加する。
- **142行目** `const render = async () => {`：定数を定義する。変化しない上限・設定値として使う。
- **143行目** `const thisRequest = ++currentRequest;`：定数を定義する。変化しない上限・設定値として使う。
- **144行目** `const code = getValue();`：定数を定義する。変化しない上限・設定値として使う。

### 145〜153行

```js
    $('#render-status').textContent = '描画中...';
    try {
      const result = await request('render', {uml:code,format:currentFormat});
      if (thisRequest !== currentRequest) return;
      lastResult = result;
      display(result, currentFormat);
      $('#render-status').textContent = result.mode === 'local' ? 'ローカルで描画しました' : 'PlantUML公式サーバーで表示';
    } catch(error) {
      if (thisRequest !== currentRequest) return;
```

- **145行目** `$('#render-status').textContent = '描画中...';`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **146行目** `try {`：失敗する可能性のある処理を開始し、失敗時はcatchへ制御が移る。
- **147行目** `const result = await request('render', {uml:code,format:currentFormat});`：定数を定義する。変化しない上限・設定値として使う。
- **148行目** `if (thisRequest !== currentRequest) return;`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **149行目** `lastResult = result;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **150行目** `display(result, currentFormat);`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **151行目** `$('#render-status').textContent = result.mode === 'local' ? 'ローカルで描画しました' : 'PlantUML公式…`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **152行目** `} catch(error) {`：先行処理が投げた例外を受け、ユーザーに表示するエラーへ変換する。
- **153行目** `if (thisRequest !== currentRequest) return;`：条件分岐。条件が真の場合にだけ対応する処理を実行する。

### 154〜162行

```js
      lastResult = null;
      setMessage($('#preview-area'), error.message, 'error');
      $('#render-status').textContent = '描画できませんでした';
    }
  };
  const onEdit = () => {
    localStorage.setItem(storageKey, getValue());
    $('#editor-state').textContent = 'ローカルに自動保存済み';
    clearTimeout(currentTimer);
```

- **154行目** `lastResult = null;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **155行目** `setMessage($('#preview-area'), error.message, 'error');`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **156行目** `$('#render-status').textContent = '描画できませんでした';`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **159行目** `const onEdit = () => {`：定数を定義する。変化しない上限・設定値として使う。
- **160行目** `localStorage.setItem(storageKey, getValue());`：同じブラウザ・同じオリジンに編集状態を保存／取得する。サーバーには送らない。
- **161行目** `$('#editor-state').textContent = 'ローカルに自動保存済み';`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **162行目** `clearTimeout(currentTimer);`：先に登録したタイマーを取り消して過剰な再描画を防ぐ。

### 163〜171行

```js
    currentTimer = setTimeout(render, 650);
  };
  textarea.addEventListener('input', onEdit);
  $('#render-button').addEventListener('click', render);
  $('#reset-button').addEventListener('click', () => {setValue(example);localStorage.removeItem(storageKey);render();});
  for (const button of document.querySelectorAll('[data-format]')) {
    button.addEventListener('click', () => {
      document.querySelectorAll('[data-format]').forEach(x => x.classList.toggle('active', x === button));
      currentFormat = button.dataset.format;
```

- **163行目** `currentTimer = setTimeout(render, 650);`：処理の実行を遅らせる。デバウンスやリソース解放に使う。
- **165行目** `textarea.addEventListener('input', onEdit);`：クリックや入力変更などのブラウザイベントにコールバックを登録する。
- **166行目** `$('#render-button').addEventListener('click', render);`：クリックや入力変更などのブラウザイベントにコールバックを登録する。
- **167行目** `$('#reset-button').addEventListener('click', () => {setValue(example);localStorage.remo…`：クリックや入力変更などのブラウザイベントにコールバックを登録する。
- **168行目** `for (const button of document.querySelectorAll('[data-format]')) {`：定数を定義する。変化しない上限・設定値として使う。
- **169行目** `button.addEventListener('click', () => {`：クリックや入力変更などのブラウザイベントにコールバックを登録する。
- **170行目** `document.querySelectorAll('[data-format]').forEach(x => x.classList.toggle('active', x …`：CSSクラスを変更し、表示・非表示や選択中の見た目を切り替える。
- **171行目** `currentFormat = button.dataset.format;`：値または属性を設定する。変数と代入される値の種類を確認する。

### 172〜180行

```js
      render();
    });
  }
  $('#download-button').addEventListener('click', async () => {
    const button = $('#download-button');
    button.disabled = true;
    try {
      if (engineLocal) {
        const response = await fetch('/api.php?action=download', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({uml:getValue(),format:currentFormat})});
```

- **172行目** `render();`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **175行目** `$('#download-button').addEventListener('click', async () => {`：非同期関数。awaitによる中断・再開が可能になる。
- **176行目** `const button = $('#download-button');`：定数を定義する。変化しない上限・設定値として使う。
- **177行目** `button.disabled = true;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **178行目** `try {`：失敗する可能性のある処理を開始し、失敗時はcatchへ制御が移る。
- **179行目** `if (engineLocal) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **180行目** `const response = await fetch('/api.php?action=download', {method:'POST', headers:{'Cont…`：定数を定義する。変化しない上限・設定値として使う。

### 181〜189行

```js
        if (!response.ok) {const data=await response.json(); throw new Error(data.error || 'ダウンロード失敗');}
        const blob = await response.blob();
        const objectURL = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = objectURL;
        anchor.download = 'diagram.' + currentFormat;
        document.body.appendChild(anchor);
        anchor.click();anchor.remove();
        setTimeout(() => URL.revokeObjectURL(objectURL),1000);
```

- **181行目** `if (!response.ok) {const data=await response.json(); throw new Error(data.error || 'ダウン…`：定数を定義する。変化しない上限・設定値として使う。
- **182行目** `const blob = await response.blob();`：定数を定義する。変化しない上限・設定値として使う。
- **183行目** `const objectURL = URL.createObjectURL(blob);`：定数を定義する。変化しない上限・設定値として使う。
- **184行目** `const anchor = document.createElement('a');`：定数を定義する。変化しない上限・設定値として使う。
- **185行目** `anchor.href = objectURL;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **186行目** `anchor.download = 'diagram.' + currentFormat;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **187行目** `document.body.appendChild(anchor);`：DOMツリーに新しい要素を追加する。
- **188行目** `anchor.click();anchor.remove();`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **189行目** `setTimeout(() => URL.revokeObjectURL(objectURL),1000);`：処理の実行を遅らせる。デバウンスやリソース解放に使う。

### 190〜198行

```js
      } else {
        const url = lastResult?.format === currentFormat && lastResult?.mode === 'remote' ? lastResult.url : null;
        if (!url) throw new Error('まず図をプレビューしてください。');
        window.open(url, '_blank', 'noopener,noreferrer');
        $('#render-status').textContent = '新しいタブから「名前を付けて保存」してください。';
      }
    } catch(error){ $('#render-status').textContent = error.message; }
    finally {button.disabled=false;}
  });
```

- **190行目** `} else {`：先の条件が満たされなかったときの分岐。
- **191行目** `const url = lastResult?.format === currentFormat && lastResult?.mode === 'remote' ? las…`：定数を定義する。変化しない上限・設定値として使う。
- **192行目** `if (!url) throw new Error('まず図をプレビューしてください。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **193行目** `window.open(url, '_blank', 'noopener,noreferrer');`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **194行目** `$('#render-status').textContent = '新しいタブから「名前を付けて保存」してください。';`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **196行目** `} catch(error){ $('#render-status').textContent = error.message; }`：先行処理が投げた例外を受け、ユーザーに表示するエラーへ変換する。
- **197行目** `finally {button.disabled=false;}`：正常・異常を問わず終了後に実行する後片付け処理。

### 199〜207行

```js
  $('#show-answer').addEventListener('click', () => {
    $('#answerbox').classList.toggle('hidden');
    $('#current-code').textContent = getValue();
    $('#reference-code').textContent = example;
    $('#show-answer').textContent = $('#answerbox').classList.contains('hidden') ? '模範解答を表示' : '模範解答を隠す';
  });
  $('#copy-answer').addEventListener('click', async () => {
    try {await navigator.clipboard.writeText(example);$('#copy-answer').textContent = 'コピーしました';}
    catch {$('#copy-answer').textContent = 'コピーできませんでした';}
```

- **199行目** `$('#show-answer').addEventListener('click', () => {`：クリックや入力変更などのブラウザイベントにコールバックを登録する。
- **200行目** `$('#answerbox').classList.toggle('hidden');`：CSSクラスを変更し、表示・非表示や選択中の見た目を切り替える。
- **201行目** `$('#current-code').textContent = getValue();`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **202行目** `$('#reference-code').textContent = example;`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **203行目** `$('#show-answer').textContent = $('#answerbox').classList.contains('hidden') ? '模範解答を表示…`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **205行目** `$('#copy-answer').addEventListener('click', async () => {`：非同期関数。awaitによる中断・再開が可能になる。
- **206行目** `try {await navigator.clipboard.writeText(example);$('#copy-answer').textContent = 'コピーし…`：失敗する可能性のある処理を開始し、失敗時はcatchへ制御が移る。
- **207行目** `catch {$('#copy-answer').textContent = 'コピーできませんでした';}`：先行処理が投げた例外を受け、ユーザーに表示するエラーへ変換する。

### 208〜216行

```js
  });
  $('#prompt-generate').addEventListener('click', async () => {
    $('#generated-code').classList.remove('hidden');
    try {
      const generated = await request('generate', {description:$('#description').value,theme:item.theme});
      pendingGenerated = generated.uml;
      $('#generated-code').textContent = pendingGenerated;
      $('#apply-generated').disabled = false;
    } catch(error) {$('#generated-code').textContent = error.message;}
```

- **209行目** `$('#prompt-generate').addEventListener('click', async () => {`：非同期関数。awaitによる中断・再開が可能になる。
- **210行目** `$('#generated-code').classList.remove('hidden');`：CSSクラスを変更し、表示・非表示や選択中の見た目を切り替える。
- **211行目** `try {`：失敗する可能性のある処理を開始し、失敗時はcatchへ制御が移る。
- **212行目** `const generated = await request('generate', {description:$('#description').value,theme:…`：定数を定義する。変化しない上限・設定値として使う。
- **213行目** `pendingGenerated = generated.uml;`：値または属性を設定する。変数と代入される値の種類を確認する。
- **214行目** `$('#generated-code').textContent = pendingGenerated;`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **215行目** `$('#apply-generated').disabled = false;`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **216行目** `} catch(error) {$('#generated-code').textContent = error.message;}`：先行処理が投げた例外を受け、ユーザーに表示するエラーへ変換する。

### 217〜225行

```js
  });
  $('#apply-generated').addEventListener('click', () => {if (pendingGenerated) {setValue(pendingGenerated);onEdit();render();}});
  render();
  // Monaco is optional. Fallback textarea remains usable offline.
  const loader = document.createElement('script');
  loader.src = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs/loader.min.js';
  loader.onload = () => {
    if (typeof window.require !== 'function') return;
    window.require.config({paths:{vs:'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs'}});
```

- **218行目** `$('#apply-generated').addEventListener('click', () => {if (pendingGenerated) {setValue(…`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **219行目** `render();`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **220行目** `// Monaco is optional. Fallback textarea remains usable offline.`：コメント。処理意図・注意事項を記し、実行結果には直接影響しない。
- **221行目** `const loader = document.createElement('script');`：定数を定義する。変化しない上限・設定値として使う。
- **222行目** `loader.src = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs/loader…`：値または属性を設定する。変数と代入される値の種類を確認する。
- **223行目** `loader.onload = () => {`：コールバック／無名関数。別処理の完了時や配列の各要素に対して実行される。
- **224行目** `if (typeof window.require !== 'function') return;`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **225行目** `window.require.config({paths:{vs:'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/…`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。

### 226〜234行

```js
    window.require(['vs/editor/editor.main'], () => {
      const container = $('#monaco-container');
      if (!container) return;
      const code = textarea.value;
      textarea.style.display = 'none';
      const host = document.createElement('div');
      host.style.cssText = 'position:absolute;inset:0';
      container.appendChild(host);
      editor = window.monaco.editor.create(host,{value:code,language:'plaintext',theme:'vs',fontSize:13,minimap:{enabled:false},automaticLayout:true,wordWrap:'on'});
```

- **226行目** `window.require(['vs/editor/editor.main'], () => {`：コールバック／無名関数。別処理の完了時や配列の各要素に対して実行される。
- **227行目** `const container = $('#monaco-container');`：定数を定義する。変化しない上限・設定値として使う。
- **228行目** `if (!container) return;`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **229行目** `const code = textarea.value;`：定数を定義する。変化しない上限・設定値として使う。
- **230行目** `textarea.style.display = 'none';`：値または属性を設定する。変数と代入される値の種類を確認する。
- **231行目** `const host = document.createElement('div');`：定数を定義する。変化しない上限・設定値として使う。
- **232行目** `host.style.cssText = 'position:absolute;inset:0';`：値または属性を設定する。変数と代入される値の種類を確認する。
- **233行目** `container.appendChild(host);`：DOMツリーに新しい要素を追加する。
- **234行目** `editor = window.monaco.editor.create(host,{value:code,language:'plaintext',theme:'vs',f…`：値または属性を設定する。変数と代入される値の種類を確認する。

### 235〜243行

```js
      editor.onDidChangeModelContent(onEdit);
      $('#editor-state').textContent = 'Monaco Editor';
    }, () => {});
  };
  loader.onerror = () => { $('#editor-state').textContent = '標準エディタ（オフライン）'; };
  document.head.appendChild(loader);
}
(async()=>{
  try {
```

- **235行目** `editor.onDidChangeModelContent(onEdit);`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **236行目** `$('#editor-state').textContent = 'Monaco Editor';`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **237行目** `}, () => {});`：コールバック／無名関数。別処理の完了時や配列の各要素に対して実行される。
- **239行目** `loader.onerror = () => { $('#editor-state').textContent = '標準エディタ（オフライン）'; };`：要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。
- **240行目** `document.head.appendChild(loader);`：DOMツリーに新しい要素を追加する。
- **242行目** `(async()=>{`：非同期関数。awaitによる中断・再開が可能になる。
- **243行目** `try {`：失敗する可能性のある処理を開始し、失敗時はcatchへ制御が移る。

### 244〜251行

```js
    const id = document.body.dataset.id;
    if (id) await initializeDetail(id);
    else await library();
  } catch(error) {
    const area = $('#preview-area');
    if (area) setMessage(area, error.message, 'error');
  }
})();
```

- **244行目** `const id = document.body.dataset.id;`：定数を定義する。変化しない上限・設定値として使う。
- **245行目** `if (id) await initializeDetail(id);`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **246行目** `else await library();`：先の条件が満たされなかったときの分岐。
- **247行目** `} catch(error) {`：先行処理が投げた例外を受け、ユーザーに表示するエラーへ変換する。
- **248行目** `const area = $('#preview-area');`：定数を定義する。変化しない上限・設定値として使う。
- **249行目** `if (area) setMessage(area, error.message, 'error');`：条件分岐。条件が真の場合にだけ対応する処理を実行する。

## 4. 実行トレース

対象の一連の処理を具体的に追う。

テキストを編集→650ms待つ→POST描画→形式に応じて`img`または`pre/iframe`へ表示する。

テスト時は、①入力値の型を確認、②関数へ値が渡る箇所を確認、③分岐を予想、④結果・例外・HTTP応答を記録する、という順序で追跡する。

## 5. このファイルの最重要ポイント

1. リクエスト関数はHTTPエラーをJSの例外にする
2. 一覧はPHPのHTMLテーブルへDOM要素を挿入する
3. 文字列は`textContent`で表示する
4. デバウンスで過剰なAPI呼出を抑える
5. リクエスト番号で古い画像の反映を防ぐ
6. ローカルとリモートでは表示方法が変わる
7. JARがあるときだけBlobダウンロードする
8. localStorageはユーザーごと・ブラウザごとの保存
9. Monacoロード失敗時にもtextareaで編集できる

## 6. 自習のヒント

まず上記の全文から関数の入口と出口だけを追い、値の型が変わる位置に印を付ける。次に、自分で1か所だけ変更し、対応する`tests/`の確認が通るか調べる。

変更を加えた場合は、この解説に含まれる全文とハッシュも更新する。`python3 scripts/build_walkthroughs.py`で再生成できる。
