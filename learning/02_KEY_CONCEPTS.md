# 02 KEY CONCEPTS — 定義・目的・実装上の使い方

## 1. HTTPとクライアント／サーバー（必須）

HTTPはブラウザとサーバーが情報をやり取りするときの約束。`GET`は主に取得、`POST`は本文を伴う処理に使う。今回、一覧取得は`GET /api.php?action=list`、描画は`POST /api.php?action=render`。JSが`fetch`を使い、PHPが`$_GET`と`php://input`を使う。HTTPの成否はステータスコードで示す。通常200、未存在404、入力エラー422、サーバー問題500。

よくある間違い：ブラウザのJavaScriptとPHPが同じプロセスで動いていると思うこと。実際はネットワーク上の別の実行環境。

## 2. JSON（必須）

JavaScriptオブジェクトをテキストへ変換したもの。`JSON.stringify({uml: code})`で文字列を作り、PHPの`json_decode`が配列に戻す。レスポンスは`json_encode`で作られ、JSの`response.json()`で扱える。

JSONは画像バイナリを直接入れられないため、JAR側で得たPNG/SVGのバイト列を`base64_encode`する。Base64は暗号化ではなく表現の変換であり、約33%ほどデータが増える。

## 3. DOM・イベント・非同期処理（必須）

DOMはHTMLのタグをブラウザ内のオブジェクトとして操作する仕組み。`document.querySelector('#preview-area')`は要素を取得し、`replaceChildren`は中身を置き換える。`addEventListener('click',...)`でユーザー操作を登録する。

`async`関数では`await fetch(...)`を使うと通信完了まで処理を中断できる。UI全体が止まるわけではない。今回、1件目の描画が遅く2件目が先に返る状況に備え、`currentRequest`という番号で古い結果を捨てる。これが**レースコンディション対策**である。

## 4. Debounce（重要）

キーを押すたびにJavaを起動するとCPU使用率が高くなる。`setTimeout(render,650)`と`clearTimeout(currentTimer)`で、最後の変更から650ms入力が途絶えたときに描画を開始する。これがデバウンス。

例：0ms、300ms、500msで文字入力をしたなら、描画開始は1,150ms付近。厳密に実行タイミングを保証するものではないが、不要な連続通信を減らせる。

## 5. PHPのクラス・例外（必須）

`DiagramRepository`は例題取得、`Renderer`はレンダリング、`PromptGenerator`は雛形生成という異なる責務を持つ。`new Renderer()`でインスタンスを作る。`validateSource`では不正な入力を検出すると`InvalidArgumentException`を投げ、`api.php`の`catch`がHTTP422に変換する。つまり例外はプログラム内部のエラー伝播手段、HTTPステータスはクライアントへの表現。

## 6. 標準入力・標準出力・子プロセス（重要）

PHPは `proc_open` を使って`java -jar ... -pipe -tsvg`を起動し、標準入力へPlantUMLソースを渡す。Javaは画像バイト列を標準出力に書くので、PHPがそれを読み取る。外部プログラムをHTTP APIの一部分として組み込む基本的な技術。

引数を配列で渡すことでシェル文字列の組立てを避けている。UML本文をコマンドライン引数として連結していない点が安全性のうえで重要。

## 7. PlantUML圧縮URL（重要）

PlantUMLの公開サーバーでは、UML文字列をDEFLATE圧縮して、独自アルファベットのBase64表現に変換したものをパスに埋め込む。

`gzdeflate(source,9)` → `base64_encode` → `strtr(標準アルファベット → PlantUML独自アルファベット)` という順番。通常の`urlencode`だけでは公式PlantUML URLにならない。

具体的にコードでは`Renderer::encode`と`Renderer::remoteUrl`が担当する。テストは作ったURLの本文を逆方向にデコードし、元のUMLと一致することを確認している。

## 8. XSS・入力検証（必須）

悪意ある文字列がHTMLとして評価されると、画面の中でスクリプトが実行される可能性がある。PHPでは`htmlspecialchars`でタグなどをエスケープし、JavaScriptでは`textContent`を使う。生成SVGは`innerHTML`に設定せず`img`の`src`として扱う。

また、外部参照を含むPlantUMLのプリプロセッサ命令を制限し、12,000バイト上限とJAR実行時間上限を設けている。これらは防御策だが、認証・資源隔離の代わりにはならない。

## 9. ローカルストレージ（重要）

`localStorage.setItem(key, code)`で編集中コードを保存し、同じブラウザ・同じサイトのページを再表示しても編集内容を再取得できる。サーバーへ保存しないので、別デバイスとの同期は行われない。機密データの保存場所として常に適切というわけでもない。

## 10. Monaco Editor（参考）

VS Codeでも利用される編集コンポーネント。CDNからロードできれば、テキストエリアをMonacoに差し替える。`editor.getValue()`で現在のテキスト、`editor.setValue()`でテキストの変更、`onDidChangeModelContent`で変更検出。オフライン時は標準textareaを使い続けるので、エディタの読み込み失敗がサービス全体の停止にならない。

## 11. PHPの公開ルート（重要）

`-t public`はWebに配信するフォルダの指定であり、プロジェクト全体をサーバーに公開するわけではない。`src/Renderer.php`などをWeb URLから直接開けない設計にすることで、プログラムの内部コードが公開される経路を減らせる。

## 12. アーキテクチャと実務の関係（重要）

`index.php`（画面）→`app.js`（操作と通信）→`api.php`（入出力境界）→`Renderer`（ビジネス処理）という階層の考え方は、図生成に限らずレポート生成・CSV処理・データ分析のWebサービスに共通している。新しい機能を追加するときは、まず「どの層に責任を持たせるか」を決めると保守しやすい。
