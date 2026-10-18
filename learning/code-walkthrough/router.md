# router — ソースコード全文と逐次解説

対象：`public/router.php`
ソースSHA-256：`aa048fffb7e5a14f6889b8bf7da8020429d852e22e4e8ee02070f3aeaf974412`

## 1. 役割と関連ファイル

PHP内蔵開発サーバー用のページ分岐と404処理を行う。

**前提知識**：URLのパス、`is_file`、`http_response_code`。

**実行例**：`/`はindex.php、`/api.php`はPHPの実ファイルへ、存在しないURLは404を返す。

## 2. ソースコード全文（省略なし）

```php
<?php
declare(strict_types=1);
// Only public/ is exposed. Reject unknown paths rather than serving index content.
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
if ($path === '/' || $path === '/index.php') {
    require __DIR__ . '/index.php';
    return true;
}
$file = __DIR__ . '/' . ltrim((string)$path, '/');
$realFile = realpath($file);
$publicRoot = realpath(__DIR__);
if ($realFile !== false && str_starts_with($realFile, $publicRoot . DIRECTORY_SEPARATOR) && is_file($realFile)) {
    return false;
}
http_response_code(404);
header('Content-Type: text/plain; charset=utf-8');
echo 'Not Found';
```

以下では実際のソースの上から下へ進み、原文を小さな範囲に分けて説明する。

## 3. 行・ブロック単位の逐次解説

### 1〜7行

```php
<?php
declare(strict_types=1);
// Only public/ is exposed. Reject unknown paths rather than serving index content.
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
if ($path === '/' || $path === '/index.php') {
    require __DIR__ . '/index.php';
    return true;
```

- **1行目** `<?php`：HTML構造の一部。開始・終了タグの対応を確認する。
- **2行目** `declare(strict_types=1);`：PHPの暗黙の型変換を制限し、引数の不正な型を早く発見する。
- **3行目** `// Only public/ is exposed. Reject unknown paths rather than serving index content.`：コメント。処理意図・注意事項を記し、実行結果には直接影響しない。
- **4行目** `$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **5行目** `if ($path === '/' || $path === '/index.php') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **6行目** `require __DIR__ . '/index.php';`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **7行目** `return true;`：関数の処理を終了し、呼出元に値を返す。

### 8〜14行

```php
}
$file = __DIR__ . '/' . ltrim((string)$path, '/');
$realFile = realpath($file);
$publicRoot = realpath(__DIR__);
if ($realFile !== false && str_starts_with($realFile, $publicRoot . DIRECTORY_SEPARATOR) && is_file($realFile)) {
    return false;
}
```

- **9行目** `$file = __DIR__ . '/' . ltrim((string)$path, '/');`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **10行目** `$realFile = realpath($file);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **11行目** `$publicRoot = realpath(__DIR__);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **12行目** `if ($realFile !== false && str_starts_with($realFile, $publicRoot . DIRECTORY_SEPARATOR…`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **13行目** `return false;`：関数の処理を終了し、呼出元に値を返す。

### 15〜17行

```php
http_response_code(404);
header('Content-Type: text/plain; charset=utf-8');
echo 'Not Found';
```

- **15行目** `http_response_code(404);`：HTTP応答のステータス番号を設定する。
- **16行目** `header('Content-Type: text/plain; charset=utf-8');`：HTTP応答ヘッダを設定する。本文より前に出力する必要がある。
- **17行目** `echo 'Not Found';`：HTTPの本文へ出力する。出力前に適切なエスケープがされているか確認する。

## 4. 実行トレース

対象の一連の処理を具体的に追う。

`/`はindex.php、`/api.php`はPHPの実ファイルへ、存在しないURLは404を返す。

テスト時は、①入力値の型を確認、②関数へ値が渡る箇所を確認、③分岐を予想、④結果・例外・HTTP応答を記録する、という順序で追跡する。

## 5. このファイルの最重要ポイント

1. 公開ルートはpublicだけである
2. ルーターはGETパラメータではなくURLのパスを確認する
3. 静的ファイルや実PHPファイルは組込サーバーへ任せる
4. 存在しないパスは404とし、意図せずindexを返さない

## 6. 自習のヒント

まず上記の全文から関数の入口と出口だけを追い、値の型が変わる位置に印を付ける。次に、自分で1か所だけ変更し、対応する`tests/`の確認が通るか調べる。

変更を加えた場合は、この解説に含まれる全文とハッシュも更新する。`python3 scripts/build_walkthroughs.py`で再生成できる。
