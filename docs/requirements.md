# 要件定義とトレーサビリティ

## 原資料と優先順位

Recursion「PlantUML Server」のスクリーンショットを一次資料とした。PlantUMLのエディタ、描画表示、ダウンロード、模範解答比較、プロアクティブプロンプトジェネレーター、一覧と詳細ページが中心要件。

| ID | 課題要求 | 実装ファイル・場所 | 確認方法 | 結果 | 備考 |
|---|---|---|---|---|---|
| R01 | UML図の一覧と選択 | `storage/examples.json`, `DiagramRepository.php`, `index.php` | unit/HTTP | PASS | 20件の例題 |
| R02 | UMLテーマを複数扱う | `examples.json` | unit | PASS | 10種類のテーマを収録 |
| R03 | コードエディタ | `index.php`, `assets/app.js` | モックUI | PASS | Monaco CDN失敗時にtextarea |
| R04 | 入力して図をプレビュー | `Renderer.php`, `api.php`, `app.js` | API/UIモック | 部分検証 | 実JARの描画結果は未検証 |
| R05 | SVG/PNG/ASCII表示 | 同上 | HTTP応答とUIモック | 部分検証 | 非対応図ではASCII不可の場合あり |
| R06 | ファイルダウンロード | `api.php?action=download`, `app.js` | HTTP /模擬Java | 部分検証 | 実JARでの生成ファイルは未検証。JARなしでは別タブ手動保存 |
| R07 | 正解例（模範コード）比較 | `examples.json`, `app.js` | モックUI | PASS | 手書きコードとのテキスト比較（画像比較なし） |
| R08 | プロンプトから雛形生成 | `PromptGenerator.php`, `api.php` | unit/HTTP/UIモック | PASS（限定的） | AIではなく構文抽出・固定テンプレート |
| R09 | 画面の基本設計（Page/Table/Problem） | `index.php`, `app.js` | HTTP/UIモック | PASS | 一覧・詳細を同一PHPで画面切替 |
| R10 | PHPサーバー | `public/api.php`, `router.php` | HTTP | PASS | 開発サーバーで動作確認 |
| R11 | 一時ファイルの削除・省ストレージ | `Renderer.php`, `app.js` | コード確認 | PASS | 標準入出力で図を生成。一時図ファイルは作らない |
| R12 | 公開環境想定 | `docs/deployment.md` | 文書確認 | 部分検証 | 実インターネット公開は未実施 |
| R13 | 学習教材・README・GitHub提出手順 | `README.md`, `learning/`, `docs/` | 最終整合性チェック | PASS | GitHubへのpushは未実施 |

## 曖昧な要件の取り扱い

- 本文にはSVG,PNG,ASCII、ダウンロード形式ではPNG,SVG,TXTと表記される。ASCIIはTXTファイルとして扱う。
- 『プロアクティブプロンプトジェネレーター』のモデル・API・認証方法は指定なし。ユーザーデータを第三者AIへ送らない**オフラインのルールベース雛形生成**を提供した。汎用自然言語から正確な図を完全自動生成する機能ではない。
- ストレージ候補にローカルストレージと一時ファイルがある。例題は静的JSON、編集内容はブラウザlocalStorage、生成画像はメモリ上のみとした。
- 『クラウドへデプロイ』とあるがインフラ・ドメイン・認証がないため、デプロイの手順のみを記述し、実際の公開は行わない。
- サーバーにPlantUML JARがない場合は公式公開サーバーにフォールバックする。これは課題要件ではなく環境依存の運用上の代替策である。外部送信が生じることを明示する。
- 図形のバイナリ描画についてPlantUML本体がこの検証環境に存在しないので未検証である。

## 非対応・今後の課題

- ユーザー認証、共有編集、永続DB保存、課金、公開版のレート制限は対象外。
- 汎用LLMを用いた自由作文→高品質UML変換は対象外。
- 画像類似度による自動採点は対象外（PlantUMLは表記揺れを許容するため）。
- MonacoのCDN読み込みを実ネットワークで検証できていない。
