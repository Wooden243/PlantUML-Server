# Renderer — ソースコード全文と逐次解説

対象：`src/Renderer.php`
ソースSHA-256：`2dcf0c21204e3d26a7a44aa18bec9fa110562ee129b859e48768e153c61fa6d6`

## 1. 役割と関連ファイル

UMLの入力検証、ローカルJava呼び出し、公式サーバーURLエンコードを担当する。

**前提知識**：PHPのクラス・例外、バイナリデータ、標準入出力、Base64/DEFLATE。

**実行例**：APIからUMLコードと形式を受け取り、ローカルなら画像バイト列、リモートなら表示URLへ変換する。

## 2. ソースコード全文（省略なし）

```php
<?php
declare(strict_types=1);

final class Renderer
{
    private string $jar;
    private string $server;
    private const MAX_SOURCE_BYTES = 12000;

    public function __construct(?string $jar = null, ?string $server = null)
    {
        $this->jar = $jar ?? (getenv('PLANTUML_JAR') ?: dirname(__DIR__) . '/tools/plantuml.jar');
        $this->server = rtrim($server ?? 'https://www.plantuml.com/plantuml', '/');
    }

    public function hasLocalEngine(): bool
    {
        return is_file($this->jar) && is_readable($this->jar);
    }

    public function validateSource(mixed $source): string
    {
        if (!is_string($source) || trim($source) === '') {
            throw new InvalidArgumentException('UMLテキストを入力してください。');
        }
        if (strlen($source) > self::MAX_SOURCE_BYTES) {
            throw new InvalidArgumentException('UMLは12,000バイト以内にしてください。');
        }
        if (str_contains($source, "\0") || preg_match('//u', $source) !== 1) {
            throw new InvalidArgumentException('有効なUTF-8テキストを入力してください。');
        }
        // Forbid all preprocessor directives: includes and advanced macros can access resources.
        if (preg_match('/^\s*!/m', $source)) {
            throw new InvalidArgumentException('このサービスでは !include などの外部読み込み・拡張命令は使えません。');
        }
        return $source;
    }

    public function validateFormat(mixed $format): string
    {
        if (!is_string($format) || !in_array($format, ['svg', 'png', 'txt'], true)) {
            throw new InvalidArgumentException('出力形式はsvg/png/txtから指定してください。');
        }
        return $format;
    }

    public function encode(string $source): string
    {
        // PlantUML uses raw DEFLATE with a custom Base64 alphabet.
        $standard = rtrim(base64_encode(gzdeflate($source, 9)), '=');
        return strtr($standard, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/', '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_');
    }

    public function remoteUrl(string $source, string $format): string
    {
        return $this->server . '/' . $this->validateFormat($format) . '/' . $this->encode($this->validateSource($source));
    }

    /** @return array{format: string, contentType: string, bytes: string} */
    public function localRender(string $source, string $format): array
    {
        $source = $this->validateSource($source);
        $format = $this->validateFormat($format);
        if (!$this->hasLocalEngine()) {
            throw new RuntimeException('PlantUML JARがありません。READMEの導入手順を確認してください。');
        }
        $cmd = ['timeout', '15s', 'java', '-Djava.awt.headless=true', '-jar', $this->jar, '-pipe', '-t' . $format];
        $pipes = [];
        $environment = ['PLANTUML_SECURITY_PROFILE' => 'SANDBOX', 'PATH' => (getenv('PATH') ?: '/usr/bin:/bin')];
        $process = proc_open($cmd, [0 => ['pipe','r'],1 => ['pipe','w'],2 => ['pipe','w']], $pipes, dirname(__DIR__), $environment);
        if (!is_resource($process)) {
            throw new RuntimeException('Javaエンジンの起動に失敗しました。');
        }
        fwrite($pipes[0], $source);
        fclose($pipes[0]);
        $bytes = stream_get_contents($pipes[1]);
        fclose($pipes[1]);
        $errors = stream_get_contents($pipes[2]);
        fclose($pipes[2]);
        $code = proc_close($process);
        if ($code !== 0 || $bytes === false || strlen($bytes) > 5000000) {
            throw new RuntimeException('図の生成に失敗しました（終了コード ' . $code . '）。' . substr(trim((string)$errors), 0, 250));
        }
        $types = ['svg' => 'image/svg+xml', 'png' => 'image/png', 'txt' => 'text/plain; charset=utf-8'];
        return ['format' => $format, 'contentType' => $types[$format], 'bytes' => $bytes];
    }
}
```

以下では実際のソースの上から下へ進み、原文を小さな範囲に分けて説明する。

## 3. 行・ブロック単位の逐次解説

### 1〜7行

```php
<?php
declare(strict_types=1);

final class Renderer
{
    private string $jar;
    private string $server;
```

- **1行目** `<?php`：HTML構造の一部。開始・終了タグの対応を確認する。
- **2行目** `declare(strict_types=1);`：PHPの暗黙の型変換を制限し、引数の不正な型を早く発見する。
- **4行目** `final class Renderer`：クラスを定義する。責務に関係するデータとメソッドをまとめる。
- **6行目** `private string $jar;`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **7行目** `private string $server;`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。

### 8〜14行

```php
    private const MAX_SOURCE_BYTES = 12000;

    public function __construct(?string $jar = null, ?string $server = null)
    {
        $this->jar = $jar ?? (getenv('PLANTUML_JAR') ?: dirname(__DIR__) . '/tools/plantuml.jar');
        $this->server = rtrim($server ?? 'https://www.plantuml.com/plantuml', '/');
    }
```

- **8行目** `private const MAX_SOURCE_BYTES = 12000;`：定数を定義する。変化しない上限・設定値として使う。
- **10行目** `public function __construct(?string $jar = null, ?string $server = null)`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。
- **12行目** `$this->jar = $jar ?? (getenv('PLANTUML_JAR') ?: dirname(__DIR__) . '/tools/plantuml.jar');`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **13行目** `$this->server = rtrim($server ?? 'https://www.plantuml.com/plantuml', '/');`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。

### 15〜21行

```php

    public function hasLocalEngine(): bool
    {
        return is_file($this->jar) && is_readable($this->jar);
    }

    public function validateSource(mixed $source): string
```

- **16行目** `public function hasLocalEngine(): bool`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。
- **18行目** `return is_file($this->jar) && is_readable($this->jar);`：関数の処理を終了し、呼出元に値を返す。
- **21行目** `public function validateSource(mixed $source): string`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。

### 22〜28行

```php
    {
        if (!is_string($source) || trim($source) === '') {
            throw new InvalidArgumentException('UMLテキストを入力してください。');
        }
        if (strlen($source) > self::MAX_SOURCE_BYTES) {
            throw new InvalidArgumentException('UMLは12,000バイト以内にしてください。');
        }
```

- **23行目** `if (!is_string($source) || trim($source) === '') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **24行目** `throw new InvalidArgumentException('UMLテキストを入力してください。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **26行目** `if (strlen($source) > self::MAX_SOURCE_BYTES) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **27行目** `throw new InvalidArgumentException('UMLは12,000バイト以内にしてください。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。

### 29〜35行

```php
        if (str_contains($source, "\0") || preg_match('//u', $source) !== 1) {
            throw new InvalidArgumentException('有効なUTF-8テキストを入力してください。');
        }
        // Forbid all preprocessor directives: includes and advanced macros can access resources.
        if (preg_match('/^\s*!/m', $source)) {
            throw new InvalidArgumentException('このサービスでは !include などの外部読み込み・拡張命令は使えません。');
        }
```

- **29行目** `if (str_contains($source, "\0") || preg_match('//u', $source) !== 1) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **30行目** `throw new InvalidArgumentException('有効なUTF-8テキストを入力してください。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **32行目** `// Forbid all preprocessor directives: includes and advanced macros can access resources.`：コメント。処理意図・注意事項を記し、実行結果には直接影響しない。
- **33行目** `if (preg_match('/^\s*!/m', $source)) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **34行目** `throw new InvalidArgumentException('このサービスでは !include などの外部読み込み・拡張命令は使えません。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。

### 36〜42行

```php
        return $source;
    }

    public function validateFormat(mixed $format): string
    {
        if (!is_string($format) || !in_array($format, ['svg', 'png', 'txt'], true)) {
            throw new InvalidArgumentException('出力形式はsvg/png/txtから指定してください。');
```

- **36行目** `return $source;`：関数の処理を終了し、呼出元に値を返す。
- **39行目** `public function validateFormat(mixed $format): string`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。
- **41行目** `if (!is_string($format) || !in_array($format, ['svg', 'png', 'txt'], true)) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **42行目** `throw new InvalidArgumentException('出力形式はsvg/png/txtから指定してください。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。

### 43〜49行

```php
        }
        return $format;
    }

    public function encode(string $source): string
    {
        // PlantUML uses raw DEFLATE with a custom Base64 alphabet.
```

- **44行目** `return $format;`：関数の処理を終了し、呼出元に値を返す。
- **47行目** `public function encode(string $source): string`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。
- **49行目** `// PlantUML uses raw DEFLATE with a custom Base64 alphabet.`：コメント。処理意図・注意事項を記し、実行結果には直接影響しない。

### 50〜56行

```php
        $standard = rtrim(base64_encode(gzdeflate($source, 9)), '=');
        return strtr($standard, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/', '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_');
    }

    public function remoteUrl(string $source, string $format): string
    {
        return $this->server . '/' . $this->validateFormat($format) . '/' . $this->encode($this->validateSource($source));
```

- **50行目** `$standard = rtrim(base64_encode(gzdeflate($source, 9)), '=');`：ソースをDEFLATE方式で圧縮し、PlantUMLのURLエンコードへ渡す。
- **51行目** `return strtr($standard, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789…`：関数の処理を終了し、呼出元に値を返す。
- **54行目** `public function remoteUrl(string $source, string $format): string`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。
- **56行目** `return $this->server . '/' . $this->validateFormat($format) . '/' . $this->encode($this…`：関数の処理を終了し、呼出元に値を返す。

### 57〜63行

```php
    }

    /** @return array{format: string, contentType: string, bytes: string} */
    public function localRender(string $source, string $format): array
    {
        $source = $this->validateSource($source);
        $format = $this->validateFormat($format);
```

- **59行目** `/** @return array{format: string, contentType: string, bytes: string} */`：コメント。処理意図・注意事項を記し、実行結果には直接影響しない。
- **60行目** `public function localRender(string $source, string $format): array`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。
- **62行目** `$source = $this->validateSource($source);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **63行目** `$format = $this->validateFormat($format);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。

### 64〜70行

```php
        if (!$this->hasLocalEngine()) {
            throw new RuntimeException('PlantUML JARがありません。READMEの導入手順を確認してください。');
        }
        $cmd = ['timeout', '15s', 'java', '-Djava.awt.headless=true', '-jar', $this->jar, '-pipe', '-t' . $format];
        $pipes = [];
        $environment = ['PLANTUML_SECURITY_PROFILE' => 'SANDBOX', 'PATH' => (getenv('PATH') ?: '/usr/bin:/bin')];
        $process = proc_open($cmd, [0 => ['pipe','r'],1 => ['pipe','w'],2 => ['pipe','w']], $pipes, dirname(__DIR__), $environment);
```

- **64行目** `if (!$this->hasLocalEngine()) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **65行目** `throw new RuntimeException('PlantUML JARがありません。READMEの導入手順を確認してください。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **67行目** `$cmd = ['timeout', '15s', 'java', '-Djava.awt.headless=true', '-jar', $this->jar, '-pip…`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **68行目** `$pipes = [];`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **69行目** `$environment = ['PLANTUML_SECURITY_PROFILE' => 'SANDBOX', 'PATH' => (getenv('PATH') ?: …`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **70行目** `$process = proc_open($cmd, [0 => ['pipe','r'],1 => ['pipe','w'],2 => ['pipe','w']], $pi…`：子プロセスを開始する。コマンド引数を配列として安全に渡す。

### 71〜77行

```php
        if (!is_resource($process)) {
            throw new RuntimeException('Javaエンジンの起動に失敗しました。');
        }
        fwrite($pipes[0], $source);
        fclose($pipes[0]);
        $bytes = stream_get_contents($pipes[1]);
        fclose($pipes[1]);
```

- **71行目** `if (!is_resource($process)) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **72行目** `throw new RuntimeException('Javaエンジンの起動に失敗しました。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **74行目** `fwrite($pipes[0], $source);`：標準入力などのストリームへデータを書き込む。
- **75行目** `fclose($pipes[0]);`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **76行目** `$bytes = stream_get_contents($pipes[1]);`：ストリームから出力データを読み取る。画像ならバイナリの可能性がある。
- **77行目** `fclose($pipes[1]);`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。

### 78〜84行

```php
        $errors = stream_get_contents($pipes[2]);
        fclose($pipes[2]);
        $code = proc_close($process);
        if ($code !== 0 || $bytes === false || strlen($bytes) > 5000000) {
            throw new RuntimeException('図の生成に失敗しました（終了コード ' . $code . '）。' . substr(trim((string)$errors), 0, 250));
        }
        $types = ['svg' => 'image/svg+xml', 'png' => 'image/png', 'txt' => 'text/plain; charset=utf-8'];
```

- **78行目** `$errors = stream_get_contents($pipes[2]);`：ストリームから出力データを読み取る。画像ならバイナリの可能性がある。
- **79行目** `fclose($pipes[2]);`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **80行目** `$code = proc_close($process);`：子プロセスの終了状態を回収する。終了コードで成否を判断する。
- **81行目** `if ($code !== 0 || $bytes === false || strlen($bytes) > 5000000) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **82行目** `throw new RuntimeException('図の生成に失敗しました（終了コード ' . $code . '）。' . substr(trim((string)$e…`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **84行目** `$types = ['svg' => 'image/svg+xml', 'png' => 'image/png', 'txt' => 'text/plain; charset…`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。

### 85〜87行

```php
        return ['format' => $format, 'contentType' => $types[$format], 'bytes' => $bytes];
    }
}
```

- **85行目** `return ['format' => $format, 'contentType' => $types[$format], 'bytes' => $bytes];`：関数の処理を終了し、呼出元に値を返す。

## 4. 実行トレース

対象の一連の処理を具体的に追う。

APIからUMLコードと形式を受け取り、ローカルなら画像バイト列、リモートなら表示URLへ変換する。

テスト時は、①入力値の型を確認、②関数へ値が渡る箇所を確認、③分岐を予想、④結果・例外・HTTP応答を記録する、という順序で追跡する。

## 5. このファイルの最重要ポイント

1. `validateSource`で空文字・最大バイト数・UTF-8・外部参照を検査する
2. `validateFormat`は`svg/png/txt`以外を拒否する
3. `gzdeflate`と`strtr`はPlantUML固有のURL表現に必要
4. `proc_open`へ配列でコマンドを渡しシェル組み立てを避ける
5. 標準入力へUMLソースを送る
6. 標準出力に画像バイナリが返る
7. 子プロセスには15秒の時間制限を設ける
8. SVGをHTMLに直接挿入せずimgとして表示する

## 6. 自習のヒント

まず上記の全文から関数の入口と出口だけを追い、値の型が変わる位置に印を付ける。次に、自分で1か所だけ変更し、対応する`tests/`の確認が通るか調べる。

変更を加えた場合は、この解説に含まれる全文とハッシュも更新する。`python3 scripts/build_walkthroughs.py`で再生成できる。
