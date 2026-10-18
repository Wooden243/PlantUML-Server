# DiagramRepository — ソースコード全文と逐次解説

対象：`src/DiagramRepository.php`
ソースSHA-256：`c60b5e3b3bed9bf9f3ba52abccc084c6c8d65e29dd648455f20c28359f954546`

## 1. 役割と関連ファイル

演習データをJSONから読み、単独取得・検索・ページネーションする。

**前提知識**：PHPの配列、`json_decode`、`array_filter`、`array_slice`。

**実行例**：20件のリストのうち、例えば3ページ目の5件を抽出し、本文を取り除いてAPIへ返す。

## 2. ソースコード全文（省略なし）

```php
<?php
declare(strict_types=1);

final class DiagramRepository
{
    /** @return array<int, array<string, mixed>> */
    public function all(): array
    {
        $path = dirname(__DIR__) . '/storage/examples.json';
        $items = json_decode((string) file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($items)) {
            throw new RuntimeException('Example data is not an array.');
        }
        return $items;
    }

    /** @return array<string,mixed>|null */
    public function find(int $id): ?array
    {
        foreach ($this->all() as $item) {
            if ($item['id'] === $id) {
                return $item;
            }
        }
        return null;
    }

    /** @return array{items: array<int, array<string, mixed>>, total: int, page: int, pages: int} */
    public function paginate(int $page, int $perPage = 5, string $keyword = ''): array
    {
        $keyword = trim($keyword);
        $all = array_values(array_filter($this->all(), static function (array $item) use ($keyword): bool {
            if ($keyword === '') {
                return true;
            }
            return stripos(($item['title'] . ' ' . $item['theme']), $keyword) !== false;
        }));
        $total = count($all);
        $pages = max(1, (int) ceil($total / $perPage));
        $page = min(max(1, $page), $pages);
        $items = array_slice($all, ($page - 1) * $perPage, $perPage);
        $items = array_map(static function (array $item): array {
            unset($item['uml'], $item['prompt']);
            return $item;
        }, $items);
        return compact('items', 'total', 'page', 'pages');
    }
}
```

以下では実際のソースの上から下へ進み、原文を小さな範囲に分けて説明する。

## 3. 行・ブロック単位の逐次解説

### 1〜7行

```php
<?php
declare(strict_types=1);

final class DiagramRepository
{
    /** @return array<int, array<string, mixed>> */
    public function all(): array
```

- **1行目** `<?php`：HTML構造の一部。開始・終了タグの対応を確認する。
- **2行目** `declare(strict_types=1);`：PHPの暗黙の型変換を制限し、引数の不正な型を早く発見する。
- **4行目** `final class DiagramRepository`：クラスを定義する。責務に関係するデータとメソッドをまとめる。
- **6行目** `/** @return array<int, array<string, mixed>> */`：コメント。処理意図・注意事項を記し、実行結果には直接影響しない。
- **7行目** `public function all(): array`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。

### 8〜14行

```php
    {
        $path = dirname(__DIR__) . '/storage/examples.json';
        $items = json_decode((string) file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($items)) {
            throw new RuntimeException('Example data is not an array.');
        }
        return $items;
```

- **9行目** `$path = dirname(__DIR__) . '/storage/examples.json';`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **10行目** `$items = json_decode((string) file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);`：JSON形式のテキストをPHP配列・値へ復元する。
- **11行目** `if (!is_array($items)) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **12行目** `throw new RuntimeException('Example data is not an array.');`：異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。
- **14行目** `return $items;`：関数の処理を終了し、呼出元に値を返す。

### 15〜21行

```php
    }

    /** @return array<string,mixed>|null */
    public function find(int $id): ?array
    {
        foreach ($this->all() as $item) {
            if ($item['id'] === $id) {
```

- **17行目** `/** @return array<string,mixed>|null */`：コメント。処理意図・注意事項を記し、実行結果には直接影響しない。
- **18行目** `public function find(int $id): ?array`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。
- **20行目** `foreach ($this->all() as $item) {`：配列の各要素を順番に取り出して処理する。
- **21行目** `if ($item['id'] === $id) {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。

### 22〜28行

```php
                return $item;
            }
        }
        return null;
    }

    /** @return array{items: array<int, array<string, mixed>>, total: int, page: int, pages: int} */
```

- **22行目** `return $item;`：関数の処理を終了し、呼出元に値を返す。
- **25行目** `return null;`：関数の処理を終了し、呼出元に値を返す。
- **28行目** `/** @return array{items: array<int, array<string, mixed>>, total: int, page: int, pages…`：コメント。処理意図・注意事項を記し、実行結果には直接影響しない。

### 29〜35行

```php
    public function paginate(int $page, int $perPage = 5, string $keyword = ''): array
    {
        $keyword = trim($keyword);
        $all = array_values(array_filter($this->all(), static function (array $item) use ($keyword): bool {
            if ($keyword === '') {
                return true;
            }
```

- **29行目** `public function paginate(int $page, int $perPage = 5, string $keyword = ''): array`：関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。
- **31行目** `$keyword = trim($keyword);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **32行目** `$all = array_values(array_filter($this->all(), static function (array $item) use ($keyw…`：配列を条件で絞り込む。検索キーワードが一致した要素を残す。
- **33行目** `if ($keyword === '') {`：条件分岐。条件が真の場合にだけ対応する処理を実行する。
- **34行目** `return true;`：関数の処理を終了し、呼出元に値を返す。

### 36〜42行

```php
            return stripos(($item['title'] . ' ' . $item['theme']), $keyword) !== false;
        }));
        $total = count($all);
        $pages = max(1, (int) ceil($total / $perPage));
        $page = min(max(1, $page), $pages);
        $items = array_slice($all, ($page - 1) * $perPage, $perPage);
        $items = array_map(static function (array $item): array {
```

- **36行目** `return stripos(($item['title'] . ' ' . $item['theme']), $keyword) !== false;`：関数の処理を終了し、呼出元に値を返す。
- **37行目** `}));`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **38行目** `$total = count($all);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **39行目** `$pages = max(1, (int) ceil($total / $perPage));`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **40行目** `$page = min(max(1, $page), $pages);`：変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。
- **41行目** `$items = array_slice($all, ($page - 1) * $perPage, $perPage);`：配列からページに対応する連続部分だけを切り出す。
- **42行目** `$items = array_map(static function (array $item): array {`：各要素を整形して新しい配列を作る。一覧の不要フィールドを除去する。

### 43〜48行

```php
            unset($item['uml'], $item['prompt']);
            return $item;
        }, $items);
        return compact('items', 'total', 'page', 'pages');
    }
}
```

- **43行目** `unset($item['uml'], $item['prompt']);`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **44行目** `return $item;`：関数の処理を終了し、呼出元に値を返す。
- **45行目** `}, $items);`：直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。
- **46行目** `return compact('items', 'total', 'page', 'pages');`：関数の処理を終了し、呼出元に値を返す。

## 4. 実行トレース

対象の一連の処理を具体的に追う。

20件のリストのうち、例えば3ページ目の5件を抽出し、本文を取り除いてAPIへ返す。

テスト時は、①入力値の型を確認、②関数へ値が渡る箇所を確認、③分岐を予想、④結果・例外・HTTP応答を記録する、という順序で追跡する。

## 5. このファイルの最重要ポイント

1. IDは数値比較して検索する
2. 入力キーワードはタイトルとテーマに照合する
3. 検索後に`array_values`でインデックスを振り直す
4. `pages`を`ceil`で計算する
5. ページ番号を有効範囲へ丸める
6. 一覧には`uml`や`prompt`の長文を含めない
7. データ編集ではなく読み取り専用の役割に限定する

## 6. 自習のヒント

まず上記の全文から関数の入口と出口だけを追い、値の型が変わる位置に印を付ける。次に、自分で1か所だけ変更し、対応する`tests/`の確認が通るか調べる。

変更を加えた場合は、この解説に含まれる全文とハッシュも更新する。`python3 scripts/build_walkthroughs.py`で再生成できる。
