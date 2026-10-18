# api — ソースコード全文と逐次解説

対象：`public/api.php`
ソースSHA-256：`f26cebbf47f3b57fc8ebad28c8468a2ef3c0545eebff0019127dd2ece67b1348`

## 1. 役割と関連ファイル

HTTPアクションの受付、入力検証、例外処理、JSON応答とバイナリダウンロードを統括する。

**前提知識**：HTTPステータス、GET/POST、JSON、ヘッダ、例外と`never`。

**実行例**：`POST?action=render`でJSONを読み、Rendererが実行した結果をHTTPレスポンスへ変換する。

## 2. ソースコード全文（省略なし）

```php
<?php
declare(strict_types=1);
require_once dirname(__DIR__) . '/src/bootstrap.php';
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');
header('Referrer-Policy: no-referrer');
header('X-Frame-Options: DENY');

function respondJson(array $data, int $status = 200): never
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
    exit;
}

try {
    $action = $_GET['action'] ?? '';
    $repo = new DiagramRepository();
    $renderer = new Renderer();
    if ($action === 'list' && $_SERVER['REQUEST_METHOD'] === 'GET') {
        respondJson($repo->paginate((int)($_GET['page'] ?? 1), 5, (string)($_GET['q'] ?? '')));
    }
    if ($action === 'detail' && $_SERVER['REQUEST_METHOD'] === 'GET') {
        $id = filter_var($_GET['id'] ?? null, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
        if ($id === false || $id === null) throw new InvalidArgumentException('IDを指定してください。');
        $item = $repo->find($id);
        if (!$item) respondJson(['error' => '図が見つかりません。'], 404);
        respondJson($item);
    }
    if ($action === 'status' && $_SERVER['REQUEST_METHOD'] === 'GET') {
        respondJson(['renderer' => $renderer->hasLocalEngine() ? 'local' : 'remote', 'hasLocalEngine' => $renderer->hasLocalEngine()]);
    }
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        respondJson(['error' => '未対応のアクションです。'], 404);
    }
    $body = file_get_contents('php://input');
    if ($body === false || strlen($body) > 20000) throw new InvalidArgumentException('リクエストが大きすぎます。');
    $data = json_decode($body, true, 32, JSON_THROW_ON_ERROR);
    if (!is_array($data)) throw new InvalidArgumentException('JSON形式の入力が必要です。');

    if ($action === 'generate') {
        $uml = (new PromptGenerator())->generate($data['description'] ?? null, $data['theme'] ?? 'シーケンス図');
        respondJson(['uml' => $uml, 'generator' => 'rule-based']);
    }
    if ($action === 'render' || $action === 'download') {
        $uml = $renderer->validateSource($data['uml'] ?? null);
        $format = $renderer->validateFormat($data['format'] ?? 'svg');
        if ($renderer->hasLocalEngine()) {
            $result = $renderer->localRender($uml, $format);
            if ($action === 'download') {
                header('Content-Type: ' . $result['contentType']);
                header('Content-Disposition: attachment; filename="diagram.' . $format . '"');
                header('Content-Security-Policy: sandbox');
                echo $result['bytes'];
                exit;
            }
            respondJson([
                'mode' => 'local',
                'format' => $format,
                'mime' => $result['contentType'],
                'base64' => base64_encode($result['bytes']),
            ]);
        }
        if ($action === 'download') {
            respondJson(['error' => 'サーバー側でのファイルダウンロードにはPlantUML JARが必要です。', 'url' => $renderer->remoteUrl($uml, $format)], 503);
        }
        respondJson(['mode' => 'remote', 'format' => $format, 'url' => $renderer->remoteUrl($uml, $format)]);
    }
    respondJson(['error' => '未対応のアクションです。'], 404);
} catch (JsonException | InvalidArgumentException $error) {
    respondJson(['error' => $error->getMessage()], 422);
} catch (Throwable $error) {
    error_log('PlantUML server error: ' . $error->getMessage());
    respondJson(['error' => 'サーバー側でエラーが発生しました。ログを確認してください。'], 500);
}
```

以下では実際のソースの上から下へ進み、原文を小さな範囲に分けて説明する。

## 3. 行・ブロック単位の逐次解説

### 1〜9行

```php
<?php
declare(strict_types=1);
require_once dirname(__DIR__) . '/src/bootstrap.php';
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');
header('Referrer-Policy: no-referrer');
header('X-Frame-Options: DENY');

function respondJson(array $data, int $status = 200): never
```

- **1行目** `<?php`：HTML構造の一部。開始・終了タグの対応を確認する。
- **2行目** `declare(strict_types=1);`：PHPの暗黙の型変換を制限し、引数の不正な型を早く発見する。
- **3行目** `require_once dirname(__DIR__) . '/src/bootstrap.php';`：別ファイルの定義を1回だけ読み込む。相対パスの基準がどこか確認する。
- **4行目** `header('X-Content-Type-Options: nosniff');`：HTTP応答ヘッダを設定する。本文より前に出力する必要がある。
- **5行目** `header('Cache-Control: no-store');`：HTTP応答ヘッダを設定する。本文より前に出力する必要がある。
- **6行目** `header('Referrer-Policy: no-referrer');`：HTTP応答ヘッダを設定する。本文より前に出力する必要がある。
- **7行目** `header('X-Frame-Options: DENY');`：HTTP応答ヘッダを設定する。本文より前に出力する必要がある。
- **9行目** `function respondJson(array $data, int $status = 200): never`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。

### 10〜18行

```php
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
    exit;
}

try {
    $action = $_GET['action'] ?? '';
```

- **11行目** `http_response_code($status);`：HTTP応答のステータス番号を設定する。
- **12行目** `header('Content-Type: application/json; charset=utf-8');`：HTTP応答ヘッダを設定する。本文より前に出力する必要がある。
- **13行目** `echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON…`：PHP配列・値をJSON文字列に変換する。
- **14行目** `exit;`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **17行目** `try {`：失敗する可能性のある処理を開始し、失敗時はcatchへ制御が移る。
- **18行目** `$action = $_GET['action'] ?? '';`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。

### 19〜27行

```php
    $repo = new DiagramRepository();
    $renderer = new Renderer();
    if ($action === 'list' && $_SERVER['REQUEST_METHOD'] === 'GET') {
        respondJson($repo->paginate((int)($_GET['page'] ?? 1), 5, (string)($_GET['q'] ?? '')));
    }
    if ($action === 'detail' && $_SERVER['REQUEST_METHOD'] === 'GET') {
        $id = filter_var($_GET['id'] ?? null, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
        if ($id === false || $id === null) throw new InvalidArgumentException('IDを指定してください。');
        $item = $repo->find($id);
```

- **19行目** `$repo = new DiagramRepository();`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **20行目** `$renderer = new Renderer();`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **21行目** `if ($action === 'list' && $_SERVER['REQUEST_METHOD'] === 'GET') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **22行目** `respondJson($repo->paginate((int)($_GET['page'] ?? 1), 5, (string)($_GET['q'] ?? '')));`：HTTPステータスとJSONボディをまとめて出力してリクエストを終了する。
- **24行目** `if ($action === 'detail' && $_SERVER['REQUEST_METHOD'] === 'GET') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **25行目** `$id = filter_var($_GET['id'] ?? null, FILTER_VALIDATE_INT, ['options' => ['min_range' =…`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **26行目** `if ($id === false || $id === null) throw new InvalidArgumentException('IDを指定してください。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **27行目** `$item = $repo->find($id);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。

### 28〜36行

```php
        if (!$item) respondJson(['error' => '図が見つかりません。'], 404);
        respondJson($item);
    }
    if ($action === 'status' && $_SERVER['REQUEST_METHOD'] === 'GET') {
        respondJson(['renderer' => $renderer->hasLocalEngine() ? 'local' : 'remote', 'hasLocalEngine' => $renderer->hasLocalEngine()]);
    }
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        respondJson(['error' => '未対応のアクションです。'], 404);
    }
```

- **28行目** `if (!$item) respondJson(['error' => '図が見つかりません。'], 404);`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **29行目** `respondJson($item);`：HTTPステータスとJSONボディをまとめて出力してリクエストを終了する。
- **31行目** `if ($action === 'status' && $_SERVER['REQUEST_METHOD'] === 'GET') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **32行目** `respondJson(['renderer' => $renderer->hasLocalEngine() ? 'local' : 'remote', 'hasLocalE…`：HTTPステータスとJSONボディをまとめて出力してリクエストを終了する。
- **34行目** `if ($_SERVER['REQUEST_METHOD'] !== 'POST') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **35行目** `respondJson(['error' => '未対応のアクションです。'], 404);`：HTTPステータスとJSONボディをまとめて出力してリクエストを終了する。

### 37〜45行

```php
    $body = file_get_contents('php://input');
    if ($body === false || strlen($body) > 20000) throw new InvalidArgumentException('リクエストが大きすぎます。');
    $data = json_decode($body, true, 32, JSON_THROW_ON_ERROR);
    if (!is_array($data)) throw new InvalidArgumentException('JSON形式の入力が必要です。');

    if ($action === 'generate') {
        $uml = (new PromptGenerator())->generate($data['description'] ?? null, $data['theme'] ?? 'シーケンス図');
        respondJson(['uml' => $uml, 'generator' => 'rule-based']);
    }
```

- **37行目** `$body = file_get_contents('php://input');`：ファイルまたはHTTP本文を文字列として取得する。
- **38行目** `if ($body === false || strlen($body) > 20000) throw new InvalidArgumentException('リクエスト…`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **39行目** `$data = json_decode($body, true, 32, JSON_THROW_ON_ERROR);`：JSON形式のテキストをPHP配列・値へ復元する。
- **40行目** `if (!is_array($data)) throw new InvalidArgumentException('JSON形式の入力が必要です。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **42行目** `if ($action === 'generate') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **43行目** `$uml = (new PromptGenerator())->generate($data['description'] ?? null, $data['theme'] ?…`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **44行目** `respondJson(['uml' => $uml, 'generator' => 'rule-based']);`：HTTPステータスとJSONボディをまとめて出力してリクエストを終了する。

### 46〜54行

```php
    if ($action === 'render' || $action === 'download') {
        $uml = $renderer->validateSource($data['uml'] ?? null);
        $format = $renderer->validateFormat($data['format'] ?? 'svg');
        if ($renderer->hasLocalEngine()) {
            $result = $renderer->localRender($uml, $format);
            if ($action === 'download') {
                header('Content-Type: ' . $result['contentType']);
                header('Content-Disposition: attachment; filename="diagram.' . $format . '"');
                header('Content-Security-Policy: sandbox');
```

- **46行目** `if ($action === 'render' || $action === 'download') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **47行目** `$uml = $renderer->validateSource($data['uml'] ?? null);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **48行目** `$format = $renderer->validateFormat($data['format'] ?? 'svg');`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **49行目** `if ($renderer->hasLocalEngine()) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **50行目** `$result = $renderer->localRender($uml, $format);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **51行目** `if ($action === 'download') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **52行目** `header('Content-Type: ' . $result['contentType']);`：HTTP応答ヘッダを設定する。本文より前に出力する必要がある。
- **53行目** `header('Content-Disposition: attachment; filename="diagram.' . $format . '"');`：HTTP応答ヘッダを設定する。本文より前に出力する必要がある。
- **54行目** `header('Content-Security-Policy: sandbox');`：HTTP応答ヘッダを設定する。本文より前に出力する必要がある。

### 55〜63行

```php
                echo $result['bytes'];
                exit;
            }
            respondJson([
                'mode' => 'local',
                'format' => $format,
                'mime' => $result['contentType'],
                'base64' => base64_encode($result['bytes']),
            ]);
```

- **55行目** `echo $result['bytes'];`：HTTPの本文へ出力する。出力前に適切なエスケープがされているか確認する。
- **56行目** `exit;`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **58行目** `respondJson([`：HTTPステータスとJSONボディをまとめて出力してリクエストを終了する。
- **59行目** `'mode' => 'local',`：コールバック／無名関数。別処理の完了時や配列の各要素に対して実行される。
- **60行目** `'format' => $format,`：コールバック／無名関数。別処理の完了時や配列の各要素に対して実行される。
- **61行目** `'mime' => $result['contentType'],`：コールバック／無名関数。別処理の完了時や配列の各要素に対して実行される。
- **62行目** `'base64' => base64_encode($result['bytes']),`：画像や圧縮バイト列をテキストとして扱える表現にする。
- **63行目** `]);`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。

### 64〜72行

```php
        }
        if ($action === 'download') {
            respondJson(['error' => 'サーバー側でのファイルダウンロードにはPlantUML JARが必要です。', 'url' => $renderer->remoteUrl($uml, $format)], 503);
        }
        respondJson(['mode' => 'remote', 'format' => $format, 'url' => $renderer->remoteUrl($uml, $format)]);
    }
    respondJson(['error' => '未対応のアクションです。'], 404);
} catch (JsonException | InvalidArgumentException $error) {
    respondJson(['error' => $error->getMessage()], 422);
```

- **65行目** `if ($action === 'download') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **66行目** `respondJson(['error' => 'サーバー側でのファイルダウンロードにはPlantUML JARが必要です。', 'url' => $renderer->re…`：HTTPステータスとJSONボディをまとめて出力してリクエストを終了する。
- **68行目** `respondJson(['mode' => 'remote', 'format' => $format, 'url' => $renderer->remoteUrl($um…`：HTTPステータスとJSONボディをまとめて出力してリクエストを終了する。
- **70行目** `respondJson(['error' => '未対応のアクションです。'], 404);`：HTTPステータスとJSONボディをまとめて出力してリクエストを終了する。
- **71行目** `} catch (JsonException | InvalidArgumentException $error) {`：先行処理が投げた例外を受け、ユーザーに表示するエラーへ変換する。
- **72行目** `respondJson(['error' => $error->getMessage()], 422);`：HTTPステータスとJSONボディをまとめて出力してリクエストを終了する。

### 73〜76行

```php
} catch (Throwable $error) {
    error_log('PlantUML server error: ' . $error->getMessage());
    respondJson(['error' => 'サーバー側でエラーが発生しました。ログを確認してください。'], 500);
}
```

- **73行目** `} catch (Throwable $error) {`：先行処理が投げた例外を受け、ユーザーに表示するエラーへ変換する。
- **74行目** `error_log('PlantUML server error: ' . $error->getMessage());`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **75行目** `respondJson(['error' => 'サーバー側でエラーが発生しました。ログを確認してください。'], 500);`：HTTPステータスとJSONボディをまとめて出力してリクエストを終了する。

## 4. 実行トレース

対象の一連の処理を具体的に追う。

`POST?action=render`でJSONを読み、Rendererが実行した結果をHTTPレスポンスへ変換する。

テスト時は、①入力値の型を確認、②関数へ値が渡る箇所を確認、③分岐を予想、④結果・例外・HTTP応答を記録する、という順序で追跡する。

## 5. このファイルの最重要ポイント

1. GETとPOSTの意味を明確に分ける
2. API成功時と失敗時でHTTPステータスを変える
3. JSONレスポンスは`Content-Type: application/json`を使う
4. リモート描画時はバイナリを送らずURLを返す
5. ローカル描画時はBase64付きJSONを返す
6. ダウンロード時はattachmentヘッダを付ける
7. 例外を500/422に変換し内部情報を漏らさない
8. PHP実行ログへ原因を残す

## 6. 自習のヒント

まず上記の全文から関数の入口と出口だけを追い、値の型が変わる位置に印を付ける。次に、自分で1か所だけ変更し、対応する`tests/`の確認が通るか調べる。

変更を加えた場合は、この解説に含まれる全文とハッシュも更新する。`python3 scripts/build_walkthroughs.py`で再生成できる。
