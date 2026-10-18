# index — ソースコード全文と逐次解説

対象：`public/index.php`
ソースSHA-256：`f522e5164f32d4a655ff028898b329244ad3354abb4c61ee9aab0b86acedbe88`

## 1. 役割と関連ファイル

サーバーサイドで一覧と演習詳細のHTML骨格を生成する。

**前提知識**：PHPとHTMLの混在、データ属性、フォーム要素、HTMLエスケープ。

**実行例**：URLに`?id=5`があれば演習詳細のDOMを作り、JavaScriptが動的な内容を取得する。

## 2. ソースコード全文（省略なし）

```php
<?php
declare(strict_types=1);
require_once dirname(__DIR__) . '/src/bootstrap.php';
$id = filter_var($_GET['id'] ?? null, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
$isDetail = $id !== false && $id !== null;
$entry = $isDetail ? (new DiagramRepository())->find((int)$id) : null;
if ($isDetail && !$entry) {
    http_response_code(404);
}
header('Content-Type: text/html; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: no-referrer');
?>
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title><?= $entry ? escapeHtml($entry['title']) . ' | ' : '' ?>PlantUML Server</title>
  <link rel="stylesheet" href="/assets/style.css">
  <script defer src="/assets/app.js"></script>
</head>
<body data-id="<?= $entry ? (int)$entry['id'] : '' ?>">
<header class="topbar"><div class="topinner"><div class="brandmark">PU</div><div><strong>PlantUML Server</strong><small>Model diagrams from text</small></div><div class="topspace"></div><span class="headerhint">UML Playground</span></div></header>
<main class="mainwrap">
<?php if (!$isDetail): ?>
  <section class="hero"><div class="eyebrow">DIAGRAM WORKSPACE</div><h1>PlantUML Server</h1><p>UML記法を使って、設計図をテキストから作成する練習環境です。</p><p class="muted">テーマ別の演習を選択し、PlantUMLを編集・プレビューできます。正解例やルールベースの作成補助も利用できます。</p></section>
  <section class="panel"><div class="sectionhead"><div><h2>図のライブラリ</h2><p class="muted">例題を選ぶとエディタと図のプレビューが開きます。</p></div><input id="search" type="search" placeholder="タイトル・テーマを検索" aria-label="図を検索"></div>
    <div class="tablewrap"><table><thead><tr><th>ID</th><th>Title</th><th>Theme</th><th></th></tr></thead><tbody id="diagram-rows"><tr><td colspan="4">読み込み中...</td></tr></tbody></table></div>
    <div class="pagination" id="pagination"></div>
  </section>
  <section class="panel info"><h2>利用にあたって</h2><p>ローカルにPlantUML JARを設置すると、SVG・PNG・ASCII（TXT）をサーバー側で生成し、ファイルを直接ダウンロードできます。JARがない場合は公式PlantUMLサーバーへのURLを使って表示します。この場合、編集内容が外部サーバーへ送られるため、機密情報を入力しないでください。</p><p><a href="/?id=1">初めての方はこちら →</a></p></section>
<?php elseif ($entry): ?>
 <a class="backlink" href="/">← ライブラリへ戻る</a>
 <div class="detailheading"><div><div class="eyebrow">EXERCISE <span><?= (int)$entry['id'] ?></span> · <?= escapeHtml($entry['theme']) ?></div><h1>ID:<?= (int)$entry['id'] ?> <?= escapeHtml($entry['title']) ?></h1></div><span class="state" id="engine-state">描画エンジン確認中</span></div>
 <div class="workspace">
   <section class="workspacecard editorpanel"><div class="toolbar"><h2>PlantUML Editor</h2><span id="editor-state" class="muted tiny">編集可能</span></div>
     <div id="monaco-container" class="editorarea"><textarea id="uml-input" spellcheck="false" aria-label="PlantUMLコード" placeholder="@startuml&#10;Alice -> Bob: hello&#10;@enduml"></textarea></div>
     <div class="toolbar bottomtools"><button type="button" id="reset-button" class="btn quiet">初期コードに戻す</button><button type="button" id="render-button" class="btn primary">プレビュー更新</button></div>
   </section>
   <section class="workspacecard"><div class="toolbar"><h2>Diagram Preview</h2><div class="tabbar" role="group" aria-label="描画形式"><button class="tab active" data-format="svg">SVG</button><button class="tab" data-format="png">PNG</button><button class="tab" data-format="txt">ASCII</button></div></div>
    <div class="previewarea" id="preview-area" aria-live="polite"><p class="muted">読み込み中...</p></div>
    <div class="toolbar bottomtools"><span id="render-status" class="muted tiny">入力後に自動更新します</span><button type="button" id="download-button" class="btn primary">図をダウンロード</button></div>
   </section>
 </div>
 <section class="panel"><div class="sectionhead"><div><h2>プロンプト練習 · 正解例と比較</h2><p class="muted">要件を読み、自分のPlantUMLを書いてから模範例を確認しましょう。</p></div></div>
   <div class="promptbox"><div class="mini-label">今回の課題</div><p id="exercise-prompt"><?= escapeHtml($entry['prompt']) ?></p></div>
   <div class="toolrow"><button class="btn quiet" id="show-answer">模範解答を表示</button><button class="btn quiet" id="copy-answer">模範解答をコピー</button></div>
   <div id="answerbox" class="hidden"><h3>模範例（テキスト比較用）</h3><div class="compare"><pre id="current-code"></pre><pre id="reference-code"></pre></div><p class="muted tiny">UMLは表記が異なっても同じ図を表せます。単純な文字列の一致を正誤判定には使用していません。</p></div>
   <div class="divider"></div><h3>ルールベース作成補助</h3><p class="muted">説明を入力すると、基本的なPlantUMLの雛形を生成します。生成AIではなく、簡易なルールに従う学習補助です。</p>
   <textarea id="description" rows="3" aria-label="作成したい図の説明" placeholder="例: Alice -> Bob: Hello"></textarea>
   <div class="toolrow"><button class="btn primary" id="prompt-generate">雛形を生成</button><button class="btn quiet" id="apply-generated" disabled>生成案をエディタへ反映</button></div>
   <pre id="generated-code" class="hidden"></pre>
 </section>
 <section class="panel"><h2>図の書き方</h2><p class="muted">多くの図は <code>@startuml</code> から始まり <code>@enduml</code> で終了します。シーケンス図では <code>A -&gt; B: message</code> がメッセージ送信です。レイアウトや要素は入力に応じて変化します。</p><p id="privacy-note" class="muted tiny"></p></section>
<?php else: ?><div class="panel"><h1>404: 図が見つかりません</h1><a href="/">ライブラリへ戻る</a></div><?php endif; ?>
</main>
<footer class="footer">PlantUML Server · Example exercises · <a href="https://plantuml.com/" target="_blank" rel="noreferrer">PlantUML documentation ↗</a></footer>
</body></html>
```

以下では実際のソースの上から下へ進み、原文を小さな範囲に分けて説明する。

## 3. 行・ブロック単位の逐次解説

### 1〜9行

```php
<?php
declare(strict_types=1);
require_once dirname(__DIR__) . '/src/bootstrap.php';
$id = filter_var($_GET['id'] ?? null, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
$isDetail = $id !== false && $id !== null;
$entry = $isDetail ? (new DiagramRepository())->find((int)$id) : null;
if ($isDetail && !$entry) {
    http_response_code(404);
}
```

- **1行目** `<?php`：HTML構造の一部。開始・終了タグの対応を確認する。
- **2行目** `declare(strict_types=1);`：PHPの暗黙の型変換を制限し、引数の不正な型を早く発見する。
- **3行目** `require_once dirname(__DIR__) . '/src/bootstrap.php';`：別ファイルの定義を1回だけ読み込む。相対パスの基準がどこか確認する。
- **4行目** `$id = filter_var($_GET['id'] ?? null, FILTER_VALIDATE_INT, ['options' => ['min_range' =…`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **5行目** `$isDetail = $id !== false && $id !== null;`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **6行目** `$entry = $isDetail ? (new DiagramRepository())->find((int)$id) : null;`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **7行目** `if ($isDetail && !$entry) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **8行目** `http_response_code(404);`：HTTP応答のステータス番号を設定する。

### 10〜18行

```php
header('Content-Type: text/html; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: no-referrer');
?>
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
```

- **10行目** `header('Content-Type: text/html; charset=utf-8');`：HTTP応答ヘッダを設定する。本文より前に出力する必要がある。
- **11行目** `header('X-Content-Type-Options: nosniff');`：HTTP応答ヘッダを設定する。本文より前に出力する必要がある。
- **12行目** `header('Referrer-Policy: no-referrer');`：HTTP応答ヘッダを設定する。本文より前に出力する必要がある。
- **13行目** `?>`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **14行目** `<!doctype html>`：HTML構造の一部。開始・終了タグの対応を確認する。
- **15行目** `<html lang="ja">`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **16行目** `<head>`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **17行目** `<meta charset="utf-8">`：HTML構造の一部。開始・終了タグの対応を確認する。
- **18行目** `<meta name="viewport" content="width=device-width,initial-scale=1">`：HTML構造の一部。開始・終了タグの対応を確認する。

### 19〜27行

```php
  <title><?= $entry ? escapeHtml($entry['title']) . ' | ' : '' ?>PlantUML Server</title>
  <link rel="stylesheet" href="/assets/style.css">
  <script defer src="/assets/app.js"></script>
</head>
<body data-id="<?= $entry ? (int)$entry['id'] : '' ?>">
<header class="topbar"><div class="topinner"><div class="brandmark">PU</div><div><strong>PlantUML Server</strong><small>Model diagrams from text</small></div><div class="topspace"></div><span class="headerhint">UML Playground</span></div></header>
<main class="mainwrap">
<?php if (!$isDetail): ?>
  <section class="hero"><div class="eyebrow">DIAGRAM WORKSPACE</div><h1>PlantUML Server</h1><p>UML記法を使って、設計図をテキストから作成する練習環境です。</p><p class="muted">テーマ別の演習を選択し、PlantUMLを編集・プレビューできます。正解例やルールベースの作成補助も利用できます。</p></section>
```

- **19行目** `<title><?= $entry ? escapeHtml($entry['title']) . ' | ' : '' ?>PlantUML Server</title>`：HTML構造の一部。開始・終了タグの対応を確認する。
- **20行目** `<link rel="stylesheet" href="/assets/style.css">`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **21行目** `<script defer src="/assets/app.js"></script>`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **22行目** `</head>`：HTML構造の一部。開始・終了タグの対応を確認する。
- **23行目** `<body data-id="<?= $entry ? (int)$entry['id'] : '' ?>">`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **24行目** `<header class="topbar"><div class="topinner"><div class="brandmark">PU</div><div><stron…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **25行目** `<main class="mainwrap">`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **26行目** `<?php if (!$isDetail): ?>`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **27行目** `<section class="hero"><div class="eyebrow">DIAGRAM WORKSPACE</div><h1>PlantUML Server</…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。

### 28〜36行

```php
  <section class="panel"><div class="sectionhead"><div><h2>図のライブラリ</h2><p class="muted">例題を選ぶとエディタと図のプレビューが開きます。</p></div><input id="search" type="search" placeholder="タイトル・テーマを検索" aria-label="図を検索"></div>
    <div class="tablewrap"><table><thead><tr><th>ID</th><th>Title</th><th>Theme</th><th></th></tr></thead><tbody id="diagram-rows"><tr><td colspan="4">読み込み中...</td></tr></tbody></table></div>
    <div class="pagination" id="pagination"></div>
  </section>
  <section class="panel info"><h2>利用にあたって</h2><p>ローカルにPlantUML JARを設置すると、SVG・PNG・ASCII（TXT）をサーバー側で生成し、ファイルを直接ダウンロードできます。JARがない場合は公式PlantUMLサーバーへのURLを使って表示します。この場合、編集内容が外部サーバーへ送られるため、機密情報を入力しないでください。</p><p><a href="/?id=1">初めての方はこちら →</a></p></section>
<?php elseif ($entry): ?>
 <a class="backlink" href="/">← ライブラリへ戻る</a>
 <div class="detailheading"><div><div class="eyebrow">EXERCISE <span><?= (int)$entry['id'] ?></span> · <?= escapeHtml($entry['theme']) ?></div><h1>ID:<?= (int)$entry['id'] ?> <?= escapeHtml($entry['title']) ?></h1></div><span class="state" id="engine-state">描画エンジン確認中</span></div>
 <div class="workspace">
```

- **28行目** `<section class="panel"><div class="sectionhead"><div><h2>図のライブラリ</h2><p class="muted">例…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **29行目** `<div class="tablewrap"><table><thead><tr><th>ID</th><th>Title</th><th>Theme</th><th></t…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **30行目** `<div class="pagination" id="pagination"></div>`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **31行目** `</section>`：HTML構造の一部。開始・終了タグの対応を確認する。
- **32行目** `<section class="panel info"><h2>利用にあたって</h2><p>ローカルにPlantUML JARを設置すると、SVG・PNG・ASCII（TX…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **33行目** `<?php elseif ($entry): ?>`：HTML構造の一部。開始・終了タグの対応を確認する。
- **34行目** `<a class="backlink" href="/">← ライブラリへ戻る</a>`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **35行目** `<div class="detailheading"><div><div class="eyebrow">EXERCISE <span><?= (int)$entry['id…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **36行目** `<div class="workspace">`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。

### 37〜45行

```php
   <section class="workspacecard editorpanel"><div class="toolbar"><h2>PlantUML Editor</h2><span id="editor-state" class="muted tiny">編集可能</span></div>
     <div id="monaco-container" class="editorarea"><textarea id="uml-input" spellcheck="false" aria-label="PlantUMLコード" placeholder="@startuml&#10;Alice -> Bob: hello&#10;@enduml"></textarea></div>
     <div class="toolbar bottomtools"><button type="button" id="reset-button" class="btn quiet">初期コードに戻す</button><button type="button" id="render-button" class="btn primary">プレビュー更新</button></div>
   </section>
   <section class="workspacecard"><div class="toolbar"><h2>Diagram Preview</h2><div class="tabbar" role="group" aria-label="描画形式"><button class="tab active" data-format="svg">SVG</button><button class="tab" data-format="png">PNG</button><button class="tab" data-format="txt">ASCII</button></div></div>
    <div class="previewarea" id="preview-area" aria-live="polite"><p class="muted">読み込み中...</p></div>
    <div class="toolbar bottomtools"><span id="render-status" class="muted tiny">入力後に自動更新します</span><button type="button" id="download-button" class="btn primary">図をダウンロード</button></div>
   </section>
 </div>
```

- **37行目** `<section class="workspacecard editorpanel"><div class="toolbar"><h2>PlantUML Editor</h2…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **38行目** `<div id="monaco-container" class="editorarea"><textarea id="uml-input" spellcheck="fals…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **39行目** `<div class="toolbar bottomtools"><button type="button" id="reset-button" class="btn qui…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **40行目** `</section>`：HTML構造の一部。開始・終了タグの対応を確認する。
- **41行目** `<section class="workspacecard"><div class="toolbar"><h2>Diagram Preview</h2><div class=…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **42行目** `<div class="previewarea" id="preview-area" aria-live="polite"><p class="muted">読み込み中...…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **43行目** `<div class="toolbar bottomtools"><span id="render-status" class="muted tiny">入力後に自動更新しま…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **44行目** `</section>`：HTML構造の一部。開始・終了タグの対応を確認する。
- **45行目** `</div>`：HTML構造の一部。開始・終了タグの対応を確認する。

### 46〜54行

```php
 <section class="panel"><div class="sectionhead"><div><h2>プロンプト練習 · 正解例と比較</h2><p class="muted">要件を読み、自分のPlantUMLを書いてから模範例を確認しましょう。</p></div></div>
   <div class="promptbox"><div class="mini-label">今回の課題</div><p id="exercise-prompt"><?= escapeHtml($entry['prompt']) ?></p></div>
   <div class="toolrow"><button class="btn quiet" id="show-answer">模範解答を表示</button><button class="btn quiet" id="copy-answer">模範解答をコピー</button></div>
   <div id="answerbox" class="hidden"><h3>模範例（テキスト比較用）</h3><div class="compare"><pre id="current-code"></pre><pre id="reference-code"></pre></div><p class="muted tiny">UMLは表記が異なっても同じ図を表せます。単純な文字列の一致を正誤判定には使用していません。</p></div>
   <div class="divider"></div><h3>ルールベース作成補助</h3><p class="muted">説明を入力すると、基本的なPlantUMLの雛形を生成します。生成AIではなく、簡易なルールに従う学習補助です。</p>
   <textarea id="description" rows="3" aria-label="作成したい図の説明" placeholder="例: Alice -> Bob: Hello"></textarea>
   <div class="toolrow"><button class="btn primary" id="prompt-generate">雛形を生成</button><button class="btn quiet" id="apply-generated" disabled>生成案をエディタへ反映</button></div>
   <pre id="generated-code" class="hidden"></pre>
 </section>
```

- **46行目** `<section class="panel"><div class="sectionhead"><div><h2>プロンプト練習 · 正解例と比較</h2><p class=…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **47行目** `<div class="promptbox"><div class="mini-label">今回の課題</div><p id="exercise-prompt"><?= e…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **48行目** `<div class="toolrow"><button class="btn quiet" id="show-answer">模範解答を表示</button><button…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **49行目** `<div id="answerbox" class="hidden"><h3>模範例（テキスト比較用）</h3><div class="compare"><pre id="c…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **50行目** `<div class="divider"></div><h3>ルールベース作成補助</h3><p class="muted">説明を入力すると、基本的なPlantUMLの雛形…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **51行目** `<textarea id="description" rows="3" aria-label="作成したい図の説明" placeholder="例: Alice -> Bob…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **52行目** `<div class="toolrow"><button class="btn primary" id="prompt-generate">雛形を生成</button><bu…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **53行目** `<pre id="generated-code" class="hidden"></pre>`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **54行目** `</section>`：HTML構造の一部。開始・終了タグの対応を確認する。

### 55〜59行

```php
 <section class="panel"><h2>図の書き方</h2><p class="muted">多くの図は <code>@startuml</code> から始まり <code>@enduml</code> で終了します。シーケンス図では <code>A -&gt; B: message</code> がメッセージ送信です。レイアウトや要素は入力に応じて変化します。</p><p id="privacy-note" class="muted tiny"></p></section>
<?php else: ?><div class="panel"><h1>404: 図が見つかりません</h1><a href="/">ライブラリへ戻る</a></div><?php endif; ?>
</main>
<footer class="footer">PlantUML Server · Example exercises · <a href="https://plantuml.com/" target="_blank" rel="noreferrer">PlantUML documentation ↗</a></footer>
</body></html>
```

- **55行目** `<section class="panel"><h2>図の書き方</h2><p class="muted">多くの図は <code>@startuml</code> から始ま…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **56行目** `<?php else: ?><div class="panel"><h1>404: 図が見つかりません</h1><a href="/">ライブラリへ戻る</a></div><…`：先の条件が満たされなかったときの分岐。
- **57行目** `</main>`：HTML構造の一部。開始・終了タグの対応を確認する。
- **58行目** `<footer class="footer">PlantUML Server · Example exercises · <a href="https://plantuml.…`：HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。
- **59行目** `</body></html>`：HTML構造の一部。開始・終了タグの対応を確認する。

## 4. 実行トレース

対象の一連の処理を具体的に追う。

URLに`?id=5`があれば演習詳細のDOMを作り、JavaScriptが動的な内容を取得する。

テスト時は、①入力値の型を確認、②関数へ値が渡る箇所を確認、③分岐を予想、④結果・例外・HTTP応答を記録する、という順序で追跡する。

## 5. このファイルの最重要ポイント

1. タイトルには`escapeHtml`を使う
2. 存在しないIDでは404を返す
3. 一覧・詳細の切替はPHPで行う
4. エディタはtextareaを最低限のフォールバックにする
5. 画像プレビューはJSが後で生成する
6. 模範解答の表示・非表示を切り替えられる
7. フォームに明確なaria-labelを与える
8. 外部リンクにはnoopener/noreferrerを検討する

## 6. 自習のヒント

まず上記の全文から関数の入口と出口だけを追い、値の型が変わる位置に印を付ける。次に、自分で1か所だけ変更し、対応する`tests/`の確認が通るか調べる。

変更を加えた場合は、この解説に含まれる全文とハッシュも更新する。`python3 scripts/build_walkthroughs.py`で再生成できる。
