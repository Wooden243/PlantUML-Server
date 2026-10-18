# bootstrap — ソースコード全文と逐次解説

対象：`src/bootstrap.php`
ソースSHA-256：`42a1d6f5c4167344905d522fdddf574111560810eb89fed053aeb103572760cf`

## 1. 役割と関連ファイル

PHPクラスの読み込みと共通HTMLエスケープ関数を提供する。

**前提知識**：require_once、関数定義、HTML特殊文字。

**実行例**：index.phpとapi.phpが同じクラスを読み込む。

## 2. ソースコード全文（省略なし）

```php
<?php
declare(strict_types=1);
require_once __DIR__ . '/DiagramRepository.php';
require_once __DIR__ . '/Renderer.php';
require_once __DIR__ . '/PromptGenerator.php';
function escapeHtml(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}
```

以下では実際のソースの上から下へ進み、原文を小さな範囲に分けて説明する。

## 3. 行・ブロック単位の逐次解説

### 1〜7行

```php
<?php
declare(strict_types=1);
require_once __DIR__ . '/DiagramRepository.php';
require_once __DIR__ . '/Renderer.php';
require_once __DIR__ . '/PromptGenerator.php';
function escapeHtml(string $value): string
{
```

- **1行目** `<?php`：HTML構造の一部。開始・終了タグの対応を確認する。
- **2行目** `declare(strict_types=1);`：PHPの暗黙の型変換を制限し、引数の不正な型を早く発見する。
- **3行目** `require_once __DIR__ . '/DiagramRepository.php';`：別ファイルの定義を1回だけ読み込む。相対パスの基準がどこか確認する。
- **4行目** `require_once __DIR__ . '/Renderer.php';`：別ファイルの定義を1回だけ読み込む。相対パスの基準がどこか確認する。
- **5行目** `require_once __DIR__ . '/PromptGenerator.php';`：別ファイルの定義を1回だけ読み込む。相対パスの基準がどこか確認する。
- **6行目** `function escapeHtml(string $value): string`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。

### 8〜9行

```php
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}
```

- **8行目** `return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');`：関数の処理を終了し、呼出元に値を返す。

## 4. 実行トレース

対象の一連の処理を具体的に追う。

index.phpとapi.phpが同じクラスを読み込む。

テスト時は、①入力値の型を確認、②関数へ値が渡る箇所を確認、③分岐を予想、④結果・例外・HTTP応答を記録する、という順序で追跡する。

## 5. このファイルの最重要ポイント

1. require_onceは重複読込を避ける
2. HTML特殊文字をエスケープしてXSSを防ぐ
3. 関数は画面表示で使い、JSONには使わない

## 6. 自習のヒント

まず上記の全文から関数の入口と出口だけを追い、値の型が変わる位置に印を付ける。次に、自分で1か所だけ変更し、対応する`tests/`の確認が通るか調べる。

変更を加えた場合は、この解説に含まれる全文とハッシュも更新する。`python3 scripts/build_walkthroughs.py`で再生成できる。
