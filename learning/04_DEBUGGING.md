# 04 DEBUGGING — エラーの調査と再現

## 1. デバッグの基本手順

1. **何をしたか**（URL、押したボタン、入力内容）を記録する。
2. **期待結果**と**実際の結果**を分ける。
3. Chrome/Edgeの開発者ツールをF12で開く。「Console」でJavaScript例外、「Network」でHTTP要求・応答を見る。
4. 問題がブラウザかHTTPかPHPかPlantUMLエンジンかを切り分ける。
5. 最小入力（例：`@startuml\nA -> B: hi\n@enduml`）で再現する。
6. 1か所ずつ変更して再テストし、解決したか確認する。

## 2. よくある症状と修正方法

### 画面が開かない / 接続できない

- `php -v`でPHPの存在確認。
- `pwd`でルートを確認。`public/`内でなくルートからコマンドを実行する。
- `php -S 127.0.0.1:8000 -t public public/router.php`を実行。
- 別プロセスが8000番ポートを使用していれば8001番を使う。
- WSL上で`curl -I http://127.0.0.1:8000/`を実行し、200が返るか確認。

### 一覧が空欄になる

- `storage/examples.json`が存在するか確認。
- `curl 'http://127.0.0.1:8000/api.php?action=list&page=1'`のJSONを確認。
- ブラウザConsoleで通信エラーを確認。
- `json_decode`が失敗した場合、例題JSONにカンマ抜けなどがないか確認。

### 図が出ない・壊れた画像アイコン

- 画面のエンジン表示が「ローカル」か「公式サーバー利用」かを確認。
- ローカルJAR時：`java -jar tools/plantuml.jar -version`、`dot -V`を確認。
- ローカルJARなし時：公式サーバーへHTTPSアクセスできるか、ブラウザのNetworkを見る。
- UMLが`@startuml`/`@enduml`で囲まれているか確認。
- `!include`や`!theme`などのプリプロセッサ命令はサービスの安全制限で拒否される。
- UMLの文法エラーはPlantUMLがエラー図として表示する場合がある。図の本文も読む。

### ASCII/TXT表示が空になる

- PlantUMLのテキスト出力はすべての図に対応するものではない。まず最小シーケンス図で確認。
- 外部レンダリング時、ブラウザやリモート側の制約でiframeが表示できない場合がある。ローカルJARを推奨。

### `HTTP 422`になる

- JSON本文が壊れていないか。
- `uml`が文字列か、空でないか、12,000バイト以下か。
- `format`が`svg`, `png`, `txt`のいずれかか。
- PlantUMLソースに`!include`など外部参照命令が含まれていないか。

### `HTTP 500`になる

- PHPサーバーのターミナルログを見る。
- Javaが存在するか、jarファイルの権限があるかを確認。
- Graphvizが必要な図では`dot -V`を確認。
- 15秒で処理が終了することがある。大きい図を小さい図に分割する。

### Monaco Editorが表示されない

- CDNが遮断されていないかをNetworkで確認。
- このアプリではオフライン時に標準のテキストエリアへ切り替わる。入力やプレビュー機能は引き続き利用できる。

### GitHubにpushできない

- `git status`を見てコミット済みか確認。
- `git remote -v`が空ならorigin未登録。
- `gh repo create`の`Name already exists`は同名リポジトリが存在する意味。URLを登録して既存へpushする。
- URL中の`<USERNAME>`はBashリダイレクトとして扱われるので、山括弧を含めず実際の文字列へ置換する。
- `git push`がrejectedならリモートの履歴を確認し、安易にforce pushしない。

## 3. 通信を手で試す

サーバー起動中に別ターミナルから実行する。

```bash
curl -s 'http://127.0.0.1:8000/api.php?action=status'
curl -s 'http://127.0.0.1:8000/api.php?action=list&page=1'

curl -s -X POST 'http://127.0.0.1:8000/api.php?action=render' \
 -H 'Content-Type: application/json' \
 --data '{"uml":"@startuml\nAlice -> Bob: Hello\n@enduml","format":"svg"}'
```

ネットワーク上の問題は`curl`で、UI問題はDevToolsで、描画エンジン問題は`java -jar ... -version`で調べると切り分けやすい。

## 4. 回帰テスト

修正後に以下を再実行する。テストが通ったかどうかだけでなく、対象機能が含まれているかを確認する。

```bash
php tests/unit.php
php tests/local_engine_mock.php
python3 tests/http_test.py
node --check public/assets/app.js
```

`tests/browser_mock_test.py`はPlaywrightとChromiumを別途必要とし、通信と図描画の実物は模擬する。レンダリング品質や公開環境の動作確認とは区別する。
