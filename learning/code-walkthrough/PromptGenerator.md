# PromptGenerator — ソースコード全文と逐次解説

対象：`src/PromptGenerator.php`
ソースSHA-256：`30bb6a071edf6132b0a748273a8bdaacd0905786a808072c823adcf52cc36146`

## 1. 役割と関連ファイル

テキストの単純なパターン認識からUMLの雛形を返す。AIではない。

**前提知識**：正規表現、テーマ分岐、文字列処理。

**実行例**：入力が`Alice -> Bob: Hello`なら、外枠の`@startuml`と`@enduml`を付けてシーケンス図のソースにする。

## 2. ソースコード全文（省略なし）

```php
<?php
declare(strict_types=1);

/** Deterministic practice helper; not an AI model. */
final class PromptGenerator
{
    public function generate(mixed $description, mixed $theme): string
    {
        if (!is_string($description) || trim($description) === '' || strlen($description) > 4000) {
            throw new InvalidArgumentException('作成したい図の説明を1〜4,000バイトで入力してください。');
        }
        $theme = is_string($theme) ? $theme : 'シーケンス図';
        if ($theme === 'クラス図') {
            preg_match_all('/(?:class|クラス)\s*[:：]?\s*([A-Za-z][A-Za-z0-9_]*)/iu', $description, $hits);
            $names = array_unique($hits[1]);
            if (!$names) $names = ['Customer', 'Order'];
            $lines = ['@startuml'];
            foreach (array_slice($names, 0, 12) as $name) $lines[] = 'class ' . $name;
            $lines[] = '@enduml';
            return implode("\n", $lines);
        }
        if ($theme === '状態図') {
            $names = $this->tokens($description);
            $a = $names[0] ?? 'Draft'; $b = $names[1] ?? 'Review';
            return "@startuml\n[*] --> $a\n$a --> $b\n$b --> [*]\n@enduml";
        }
        if ($theme === 'アクティビティ図') {
            $steps = preg_split('/[。\n;]+/u', trim($description)) ?: [];
            $lines = ['@startuml', 'start'];
            foreach (array_slice($steps, 0, 8) as $step) {
                $step = str_replace([':', ';'], ' ', trim($step));
                if ($step !== '') $lines[] = ':' . substr($step, 0, 70) . ';';
            }
            $lines[] = 'stop'; $lines[] = '@enduml';
            return implode("\n", $lines);
        }
        if ($theme === 'マインドマップ') {
            $steps = preg_split('/[、,。\n]+/u', trim($description)) ?: [];
            $lines = ['@startmindmap', '* Topic'];
            foreach (array_slice($steps, 0, 10) as $step) {
                $step = str_replace(["\r", "\n"], ' ', trim($step));
                if ($step !== '') $lines[] = '** ' . substr($step, 0, 80);
            }
            $lines[] = '@endmindmap';
            return implode("\n", $lines);
        }
        // Sequence diagrams: extract explicit 'A -> B: message' lines or create a starter.
        preg_match_all('/^\s*([A-Za-z][A-Za-z0-9_]*)\s*(-+>|-->|->>)\s*([A-Za-z][A-Za-z0-9_]*)\s*:\s*([^\r\n]+)/m', $description, $matches, PREG_SET_ORDER);
        if ($matches) {
            $lines = ['@startuml'];
            foreach (array_slice($matches, 0, 15) as $match) {
                $lines[] = $match[1] . ' ' . $match[2] . ' ' . $match[3] . ': ' . str_replace(['\r','\n'], ' ', trim($match[4]));
            }
            $lines[] = '@enduml';
            return implode("\n", $lines);
        }
        $names = $this->tokens($description);
        $a = $names[0] ?? 'Alice'; $b = $names[1] ?? 'Bob';
        if ($a === $b) $b = 'System';
        return "@startuml\n$a -> $b: request\n$b --> $a: response\n@enduml";
    }

    /** @return string[] */
    private function tokens(string $text): array
    {
        preg_match_all('/\b[A-Z][A-Za-z0-9_]{2,}\b/', $text, $matches);
        return array_values(array_unique(array_slice($matches[0], 0, 2)));
    }
}
```

以下では実際のソースの上から下へ進み、原文を小さな範囲に分けて説明する。

## 3. 行・ブロック単位の逐次解説

### 1〜7行

```php
<?php
declare(strict_types=1);

/** Deterministic practice helper; not an AI model. */
final class PromptGenerator
{
    public function generate(mixed $description, mixed $theme): string
```

- **1行目** `<?php`：HTML構造の一部。開始・終了タグの対応を確認する。
- **2行目** `declare(strict_types=1);`：PHPの暗黙の型変換を制限し、引数の不正な型を早く発見する。
- **4行目** `/** Deterministic practice helper; not an AI model. */`：コメント。処理意図・注意事項を記し、実行結果には直接影響しない。
- **5行目** `final class PromptGenerator`：クラスを定義する。責務に関係するデータとメソッドをまとめる。
- **7行目** `public function generate(mixed $description, mixed $theme): string`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。

### 8〜14行

```php
    {
        if (!is_string($description) || trim($description) === '' || strlen($description) > 4000) {
            throw new InvalidArgumentException('作成したい図の説明を1〜4,000バイトで入力してください。');
        }
        $theme = is_string($theme) ? $theme : 'シーケンス図';
        if ($theme === 'クラス図') {
            preg_match_all('/(?:class|クラス)\s*[:：]?\s*([A-Za-z][A-Za-z0-9_]*)/iu', $description, $hits);
```

- **9行目** `if (!is_string($description) || trim($description) === '' || strlen($description) > 400…`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **10行目** `throw new InvalidArgumentException('作成したい図の説明を1〜4,000バイトで入力してください。');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **12行目** `$theme = is_string($theme) ? $theme : 'シーケンス図';`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **13行目** `if ($theme === 'クラス図') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **14行目** `preg_match_all('/(?:class|クラス)\s*[:：]?\s*([A-Za-z][A-Za-z0-9_]*)/iu', $description, $hi…`：正規表現で文字列に特定パターンが含まれるか調べる。

### 15〜21行

```php
            $names = array_unique($hits[1]);
            if (!$names) $names = ['Customer', 'Order'];
            $lines = ['@startuml'];
            foreach (array_slice($names, 0, 12) as $name) $lines[] = 'class ' . $name;
            $lines[] = '@enduml';
            return implode("\n", $lines);
        }
```

- **15行目** `$names = array_unique($hits[1]);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **16行目** `if (!$names) $names = ['Customer', 'Order'];`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **17行目** `$lines = ['@startuml'];`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **18行目** `foreach (array_slice($names, 0, 12) as $name) $lines[] = 'class ' . $name;`：配列の各要素を順番に取り出して処理する。
- **19行目** `$lines[] = '@enduml';`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **20行目** `return implode("\n", $lines);`：関数の処理を終了し、呼出元に値を返す。

### 22〜28行

```php
        if ($theme === '状態図') {
            $names = $this->tokens($description);
            $a = $names[0] ?? 'Draft'; $b = $names[1] ?? 'Review';
            return "@startuml\n[*] --> $a\n$a --> $b\n$b --> [*]\n@enduml";
        }
        if ($theme === 'アクティビティ図') {
            $steps = preg_split('/[。\n;]+/u', trim($description)) ?: [];
```

- **22行目** `if ($theme === '状態図') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **23行目** `$names = $this->tokens($description);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **24行目** `$a = $names[0] ?? 'Draft'; $b = $names[1] ?? 'Review';`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **25行目** `return "@startuml\n[*] --> $a\n$a --> $b\n$b --> [*]\n@enduml";`：関数の処理を終了し、呼出元に値を返す。
- **27行目** `if ($theme === 'アクティビティ図') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **28行目** `$steps = preg_split('/[。\n;]+/u', trim($description)) ?: [];`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。

### 29〜35行

```php
            $lines = ['@startuml', 'start'];
            foreach (array_slice($steps, 0, 8) as $step) {
                $step = str_replace([':', ';'], ' ', trim($step));
                if ($step !== '') $lines[] = ':' . substr($step, 0, 70) . ';';
            }
            $lines[] = 'stop'; $lines[] = '@enduml';
            return implode("\n", $lines);
```

- **29行目** `$lines = ['@startuml', 'start'];`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **30行目** `foreach (array_slice($steps, 0, 8) as $step) {`：配列の各要素を順番に取り出して処理する。
- **31行目** `$step = str_replace([':', ';'], ' ', trim($step));`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **32行目** `if ($step !== '') $lines[] = ':' . substr($step, 0, 70) . ';';`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **34行目** `$lines[] = 'stop'; $lines[] = '@enduml';`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **35行目** `return implode("\n", $lines);`：関数の処理を終了し、呼出元に値を返す。

### 36〜42行

```php
        }
        if ($theme === 'マインドマップ') {
            $steps = preg_split('/[、,。\n]+/u', trim($description)) ?: [];
            $lines = ['@startmindmap', '* Topic'];
            foreach (array_slice($steps, 0, 10) as $step) {
                $step = str_replace(["\r", "\n"], ' ', trim($step));
                if ($step !== '') $lines[] = '** ' . substr($step, 0, 80);
```

- **37行目** `if ($theme === 'マインドマップ') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **38行目** `$steps = preg_split('/[、,。\n]+/u', trim($description)) ?: [];`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **39行目** `$lines = ['@startmindmap', '* Topic'];`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **40行目** `foreach (array_slice($steps, 0, 10) as $step) {`：配列の各要素を順番に取り出して処理する。
- **41行目** `$step = str_replace(["\r", "\n"], ' ', trim($step));`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **42行目** `if ($step !== '') $lines[] = '** ' . substr($step, 0, 80);`：条件分岐。条件が真の場合にだけ対応する処理を実行する。

### 43〜49行

```php
            }
            $lines[] = '@endmindmap';
            return implode("\n", $lines);
        }
        // Sequence diagrams: extract explicit 'A -> B: message' lines or create a starter.
        preg_match_all('/^\s*([A-Za-z][A-Za-z0-9_]*)\s*(-+>|-->|->>)\s*([A-Za-z][A-Za-z0-9_]*)\s*:\s*([^\r\n]+)/m', $description, $matches, PREG_SET_ORDER);
        if ($matches) {
```

- **44行目** `$lines[] = '@endmindmap';`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **45行目** `return implode("\n", $lines);`：関数の処理を終了し、呼出元に値を返す。
- **47行目** `// Sequence diagrams: extract explicit 'A -> B: message' lines or create a starter.`：コメント。処理意図・注意事項を記し、実行結果には直接影響しない。
- **48行目** `preg_match_all('/^\s*([A-Za-z][A-Za-z0-9_]*)\s*(-+>|-->|->>)\s*([A-Za-z][A-Za-z0-9_]*)\…`：正規表現で文字列に特定パターンが含まれるか調べる。
- **49行目** `if ($matches) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。

### 50〜56行

```php
            $lines = ['@startuml'];
            foreach (array_slice($matches, 0, 15) as $match) {
                $lines[] = $match[1] . ' ' . $match[2] . ' ' . $match[3] . ': ' . str_replace(['\r','\n'], ' ', trim($match[4]));
            }
            $lines[] = '@enduml';
            return implode("\n", $lines);
        }
```

- **50行目** `$lines = ['@startuml'];`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **51行目** `foreach (array_slice($matches, 0, 15) as $match) {`：配列の各要素を順番に取り出して処理する。
- **52行目** `$lines[] = $match[1] . ' ' . $match[2] . ' ' . $match[3] . ': ' . str_replace(['\r','\n…`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **54行目** `$lines[] = '@enduml';`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **55行目** `return implode("\n", $lines);`：関数の処理を終了し、呼出元に値を返す。

### 57〜63行

```php
        $names = $this->tokens($description);
        $a = $names[0] ?? 'Alice'; $b = $names[1] ?? 'Bob';
        if ($a === $b) $b = 'System';
        return "@startuml\n$a -> $b: request\n$b --> $a: response\n@enduml";
    }

    /** @return string[] */
```

- **57行目** `$names = $this->tokens($description);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **58行目** `$a = $names[0] ?? 'Alice'; $b = $names[1] ?? 'Bob';`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **59行目** `if ($a === $b) $b = 'System';`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **60行目** `return "@startuml\n$a -> $b: request\n$b --> $a: response\n@enduml";`：関数の処理を終了し、呼出元に値を返す。
- **63行目** `/** @return string[] */`：コメント。処理意図・注意事項を記し、実行結果には直接影響しない。

### 64〜69行

```php
    private function tokens(string $text): array
    {
        preg_match_all('/\b[A-Z][A-Za-z0-9_]{2,}\b/', $text, $matches);
        return array_values(array_unique(array_slice($matches[0], 0, 2)));
    }
}
```

- **64行目** `private function tokens(string $text): array`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。
- **66行目** `preg_match_all('/\b[A-Z][A-Za-z0-9_]{2,}\b/', $text, $matches);`：正規表現で文字列に特定パターンが含まれるか調べる。
- **67行目** `return array_values(array_unique(array_slice($matches[0], 0, 2)));`：関数の処理を終了し、呼出元に値を返す。

## 4. 実行トレース

対象の一連の処理を具体的に追う。

入力が`Alice -> Bob: Hello`なら、外枠の`@startuml`と`@enduml`を付けてシーケンス図のソースにする。

テスト時は、①入力値の型を確認、②関数へ値が渡る箇所を確認、③分岐を予想、④結果・例外・HTTP応答を記録する、という順序で追跡する。

## 5. このファイルの最重要ポイント

1. テーマによって雛形の構文を分岐する
2. クラス図は`class Name`の明示的な語を抽出する
3. 状態図は既存の英単語を初期ノードに当てはめる
4. アクティビティ図は文の区切りをステップとみなす
5. 矢印構文は正規表現で抽出する
6. 自由な日本語の意図をAIで理解する機能はない
7. 生成案は必ず編集して検証する

## 6. 自習のヒント

まず上記の全文から関数の入口と出口だけを追い、値の型が変わる位置に印を付ける。次に、自分で1か所だけ変更し、対応する`tests/`の確認が通るか調べる。

変更を加えた場合は、この解説に含まれる全文とハッシュも更新する。`python3 scripts/build_walkthroughs.py`で再生成できる。
