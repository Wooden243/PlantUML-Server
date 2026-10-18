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
