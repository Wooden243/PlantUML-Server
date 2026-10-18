# PlantUML Server

テキストでUMLを記述し、図としてプレビューしながら学習するPHP Webアプリケーションです。Recursion「PlantUML Server」課題をもとに作成しました。

- 20件のサンプル図（シーケンス図、クラス図、ユースケース図、アクティビティ図、状態図、コンポーネント図、デプロイ図、ネットワーク図、ガントチャート、マインドマップ）
- 一覧表示、検索、5件ずつのページネーション、詳細画面
- PlantUMLエディタ（オンラインならMonaco、オフラインは標準`textarea`）
- 入力から650ミリ秒後の自動更新、手動のプレビュー更新
- SVG、PNG、ASCII/TXTのプレビュー切替とダウンロード
- 演習文、模範コードの表示・コピー、手書きコードとのテキスト比較
- **ルールベース**の雛形生成補助（生成AIや文章理解モデルではありません）
- 編集コードはブラウザの `localStorage` に保存。全ユーザー共有DBへ書き込みません。

## 重要：描画エンジンについて

実際のUML画像はPlantUMLエンジンで描画します。**このZIPに`plantuml.jar`は同梱していません**（ライセンス・配布サイズとバージョン管理のため）。

| 環境 | プレビュー | ダウンロード | プライバシー |
|---|---|---|---|
| `tools/plantuml.jar`あり | PHPがJava+JARでSVG/PNG/TXTを生成 | 直接ダウンロード | UMLを外部送信しない |
| JARなし + インターネットあり | 公式PlantUMLサーバーへの描画URLで表示 | 別タブを開いて手動保存 | **UML本文が外部サーバーへ送信される** |
| JARなし + オフライン | UML本文・一覧・学習補助は動作 | 図の生成・ダウンロード不可 | データ送信なし |

**ローカル動作を安定させるため、JARの導入を推奨します。** ASCII出力はPlantUMLの種類・バージョンによって非対応の場合があります。ASCIIは特にシーケンス図で試してください。

## 1. 必要な環境（Windows + WSL2 Ubuntu）

- PHP **8.1以上**（本環境ではPHP 8.4.24）とzlib拡張
- ローカルで図を生成する場合、Java **17以上**とPlantUML JAR
- 一部の図のレンダリングにGraphviz（`dot`）
- Chromium / Chrome / Edgeなどのブラウザ
- インターネット（MonacoエディタまたはJARの取得時。起動そのものには不要）

WSL Ubuntuで以下のコマンドを実行してください。

```bash
sudo apt update
sudo apt install -y php-cli openjdk-17-jre-headless graphviz curl unzip
php -v
java -version
dot -V
```

`php -m` で `zlib` が利用できることを確認してください。`mbstring` は必須ではありません。Node.js・Composer・npm・データベースは不要です。

### JARをセットアップする

プロジェクトのルート（`README.md` と `public/` のあるディレクトリ）で以下を実行します。

```bash
mkdir -p tools
curl -fL https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar -o tools/plantuml.jar
java -jar tools/plantuml.jar -version
```

ダウンロード先のファイルが実行できない場合は、[PlantUML公式サイト](https://plantuml.com/download)からJARを取得し、`tools/plantuml.jar` に置いてください。JARが別の場所にある場合、以下の環境変数で指定できます。

```bash
export PLANTUML_JAR=/absolute/path/to/plantuml.jar
```

**JARをGitHubにpushする必要はありません。** `.gitignore` により `tools/*.jar` は除外されます。Javaはサーバー側で使用されます。PHPの子プロセスには `PLANTUML_SECURITY_PROFILE=SANDBOX` を設定し、最大15秒で終了するようにしています。

## 2. 起動・終了

```bash
# ZIPを展開したプロジェクト直下にいることを確認
pwd
php -S 127.0.0.1:8000 -t public public/router.php
```

Windows側のブラウザから `http://localhost:8000/` を開いてください。演習への直接リンク例：`http://localhost:8000/?id=5`。

- サーバーを終了するにはターミナルで `Ctrl+C`
- ポートが使用中なら `8000` を `8001` に変更
- デフォルト画面に戻るには「ライブラリへ戻る」をクリック
- プレビューが外部に送信されるかどうかは画面上部のステータスに表示

**WindowsパスとWSLパスの関係**：Windowsのダウンロードフォルダに展開した場合は `/mnt/c/Users/YOUR_USERNAME/Downloads/PlantUML-Server` などからアクセスできます。学習・実行はWSLホーム以下にコピーして行うとファイルアクセスが快適です。

### 例題の使い方

1. 一覧でタイトルを選ぶ。例：`ID:5 ライフラインの活性化`。
2. 左側のエディタの`@startuml`〜`@enduml`を編集する。
3. 右側の図が自動更新される。SVG/PNG/ASCIIを切り替える。
4. 「図をダウンロード」でファイルを保存する（JARありの場合）。
5. 課題文を読んでから「模範解答を表示」で参照コードと比較する。
6. 「ルールベース作成補助」で基本コードの雛形を生成する。

プログラムは**正解コードと文字列一致しなくても、同じ図を表せれば正解になり得ます**。比較結果は学習用の参考です。

## 3. テスト

**基本テスト（追加依存なし）**

```bash
php tests/unit.php
php tests/local_engine_mock.php
python3 tests/http_test.py
python3 tests/http_local_mock_test.py
```

HTTPテストはポートが空いているかを調べ、PHP内蔵サーバーをテスト中だけ起動します。`local_engine_mock.php` は実際のJARの代わりに模擬Javaコマンドを使用し、PHPのプロセス起動・標準出力取得処理を検証します。**実際のPlantUML描画を検証するテストではありません。**

**オプション：Chromiumの画面テスト（モックAPI）**

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
python3 tests/browser_mock_test.py
```

このUIテストはChromiumとPlaywrightが必要で、模擬API・模擬SVGを使ってボタン操作、一覧、検索、レスポンシブ表示を確認します。実際のPlantUML画像レンダリング・ネットワーク接続は対象外です。`docs/screenshot-*.png` もこのUIモックテストから取得した参考画面で、**描画画像は模擬SVGです**。

## 4. ディレクトリ

```text
PlantUML-Server/
├── README.md
├── .gitignore
├── public/                     # Web公開ルート（ここだけを公開）
│   ├── index.php              # 一覧・演習画面
│   ├── api.php                # JSON API / 図レンダリング
│   ├── router.php             # PHP内蔵サーバー用のルーティング
│   └── assets/
│       ├── app.js             # フロントエンドの制御
│       └── style.css          # レイアウト・モバイル対応
├── src/
│   ├── bootstrap.php          # PHPクラス読み込み・HTMLエスケープ
│   ├── DiagramRepository.php  # 例題の検索・ページング
│   ├── Renderer.php           # PlantUMLローカル/リモート描画
│   └── PromptGenerator.php    # 非AIの練習用雛形生成
├── storage/
│   └── examples.json          # 20件の演習データ
├── tools/                     # plantuml.jarの設置先（JAR自体は除外）
├── data/                      # 将来の一時データ用（現状ファイル書込なし）
├── tests/                     # PHP / HTTP / Chromiumモックテスト
├── docs/                      # 要件、検証報告、公開方法、模擬画面
└── learning/                  # 自習教材一式
    └── code-walkthrough/      # 主要ファイルの全文付き解説
```

## 5. API

- `GET /api.php?action=list&page=1&q=...` → ページネーションされた例題のJSON
- `GET /api.php?action=detail&id=5` → 指定例題のタイトル・テーマ・UMLコード・課題文
- `GET /api.php?action=status` → JARがあるかどうか
- `POST /api.php?action=render` + JSON `{ "uml": "@startuml\nAlice -> Bob\n@enduml", "format": "svg" }` → レンダリング結果のメタデータ（JARがあればBase64付き、なければPlantUML公式URL）
- `POST /api.php?action=download` + 同上JSON → ローカルJAR使用時のみ添付ファイル
- `POST /api.php?action=generate` + JSON `{ "description": "Alice -> Bob: hi", "theme": "シーケンス図" }` → ルールベースの雛形

失敗時はJSON `{ "error": "..." }` と適切なHTTPステータスを返します。JARがないときのサーバー側ファイルDLはHTTP 503を返し、代替URLをJSONに含めます。

## 6. セキュリティと制約

- `public/` 以外を公開しない設計。`storage/`、`tools/` や学習教材はWebから直接取得できません。
- 未信頼データはHTMLエスケープして表示。UMLから生成したSVGはブラウザの`img`経由で表示し、直接HTMLに埋め込みません。
- 12,000バイトまでのUTF-8ソース、SVG/PNG/TXTのみ許可。`!include`等の外部参照命令は無効化。
- PHP側の実行時間を15秒に制限し、JARの実行環境はPlantUMLのSANDBOXに設定。
- 認証・ユーザーアカウント・マルチユーザー共有編集・履歴同期は課題要件外で実装していません。
- **認証やレート制限がないため、誰でも編集可能な本番サービスとしてそのまま大規模公開しないでください。** 公開する場合はリバースプロキシのレート制限・認証・監視・ログローテーション・ファイル権限制限を追加してください。
- 公開環境では`php -S`を使わず、Nginx+PHP-FPMなどを利用してください。
- 外部PlantUMLサーバー利用時は機密情報を入力しないでください。

## 7. GitHubへの公開（まだ実行していません）

```bash
git init
git branch -M main
git status
git add .
git commit -m "Build PlantUML Server"
gh auth status
gh repo create PlantUML-Server --public --source=. --remote=origin --push
```

`gh auth status`が未認証なら先に`gh auth login`を実行してください。同名のリポジトリが**既にある**場合、`gh repo create`は失敗します。この場合は（`YOUR_USERNAME`を実際のアカウント名に書き換えて）接続します。

```bash
git remote -v
git remote add origin https://github.com/YOUR_USERNAME/PlantUML-Server.git
git push -u origin main
```

`origin`が既に登録されている場合は`git remote add`を繰り返さないでください。`git remote set-url origin https://github.com/YOUR_USERNAME/PlantUML-Server.git`を使用します。GitHub側に別の履歴がある場合、`git push`が拒否されることがあります。`--force`は安易に使用しないでください。

### HTTPSとSSH

- HTTPS接続：`https://github.com/YOUR_USERNAME/PlantUML-Server.git`。GitHub CLIに認証情報を預けられる。
- SSH接続：`git@github.com:YOUR_USERNAME/PlantUML-Server.git`。先にSSH鍵の作成とGitHubへの公開鍵登録が必要。
- `git remote -v`で送信先、`git branch -vv`で追跡関係、`git status`で未コミット変更を確認します。

Recursionの提出画面には公開GitHubリポジトリのURLを貼ってください。GitHubへのpush・Recursion提出はユーザー自身で行ってください。

## 8. 学習教材を読む順番

- **最短15分**：`learning/00_START_HERE.md` → `learning/03_EXECUTION_FLOW.md`
- **30分**：加えて`learning/01_ARCHITECTURE.md`、`learning/code-walkthrough/Renderer.md`
- **60分以上**：`learning/02_KEY_CONCEPTS.md`、`learning/code-walkthrough/app.js.md`、`learning/05_REVIEW.md`
- すべての主要ソースは`learning/code-walkthrough/`で全文と詳細解説を提供。

## 9. 参照資料

- [PlantUML公式ドキュメント](https://plantuml.com/)
- [PlantUML Download](https://plantuml.com/download)
- [PlantUML Text Encoding](https://plantuml.com/text-encoding)
- [PlantUML Security](https://plantuml.com/security)
- [Monaco Editor](https://microsoft.github.io/monaco-editor/)
- [PHP proc_open](https://www.php.net/manual/en/function.proc-open.php)
- [MDN Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)

**ライセンスについて**：本プロジェクトのソースコードのみを配布しています。PlantUML JARおよびMonaco Editor本体は同梱しません。それぞれの配布元の規約を確認してください。
