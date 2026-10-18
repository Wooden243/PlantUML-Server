# テスト報告書

## 検証対象

ソース一式（PHP 8.4.24、JavaScript Node.js 22構文チェック、Python 3.13 HTTPテスト）。検証日は2026-10-18。

## 実行と判定

| 検証 | コマンド | 結果 |
|---|---|---|
| PHP単体テスト（リポジトリ、データ、入力、圧縮URL、プロンプト） | `php tests/unit.php` | 79 PASS / 0 FAIL |
| PHP HTTPテスト（API、HTTPステータス、静的ファイル、セキュリティ） | `python3 tests/http_test.py` | 25 PASS / 0 FAIL |
| Java起動・標準出力の呼び出し経路 | `php tests/local_engine_mock.php` | 1 PASS（模擬実行バイナリによる） |
| モックJavaによるHTTP描画・ダウンロード | `python3 tests/http_local_mock_test.py` | 1 PASS（模擬SVGバイト列による） |
| ブラウザ画面のモックUIテスト | `python3 tests/browser_mock_test.py` | PASS（Chromium、模擬API・模擬SVG） |
| PHP構文 | `find ... php -l` | 全対象ファイル PASS |
| JavaScript構文 | `node --check public/assets/app.js` | PASS |
| 実際のPlantUMLでSVG/PNG/TXT生成 | JARがコンテナに存在せず | **未実施** |
| 公式PlantUMLサーバーへの実画像アクセス | ネットワーク制限で実施不可 | **未実施** |
| Monaco EditorのCDN取得 | ネットワーク制限で実施不可 | **未実施** |
| Recursionの自動採点 | 外部環境へのアクセスなし | **未実施** |
| WSL Ubuntuでのユーザー手元実行 | 別環境のため不可 | **未実施** |

## 実際に通過した主な検査

- 一覧20件、5件ページネーション、検索、IDの欠番・存在しないIDへの応答
- レンダリングフォーマット `svg/png/txt` の入力検証
- PlantUMLソースのカスタム圧縮・URLエンコーディングを逆変換して一致を検証
- UTF-8不正・NUL・過大入力・空入力・外部読み込みディレクティブを拒否
- ソースコードがHTTP公開ルート外から取得できないこと
- PNG/SVG/TXTそれぞれのAPI結果の形式
- PHPの子プロセス標準入力→模擬Java標準出力の取得
- モックUIでボタン、模範解答、リセット、雛形生成、レイアウトを検証

## 正確性の注意

UIテストはネットワーク要求を**すべて模擬**したので、実PlantUMLが図を描けることの確認にはなっていません。モック画面の画像も実PlantUMLから生成したものではありません。

実PlantUMLを導入したら、サンプルID 1,5,7,9,10,14,15をSVGとPNGで、ID 1,5をTXTで実際にレンダリングし、生成ファイルをブラウザで開いて目視確認してください。
