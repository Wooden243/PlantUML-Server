#!/usr/bin/env python3
"""Synchronize full source code and detailed block-by-block Japanese notes."""
from pathlib import Path
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT/'learning/code-walkthrough'
SOURCES = {
 'Renderer':('src/Renderer.php','UMLの入力検証、ローカルJava呼び出し、公式サーバーURLエンコードを担当する。','PHPのクラス・例外、バイナリデータ、標準入出力、Base64/DEFLATE。','APIからUMLコードと形式を受け取り、ローカルなら画像バイト列、リモートなら表示URLへ変換する。',
   ['`validateSource`で空文字・最大バイト数・UTF-8・外部参照を検査する','`validateFormat`は`svg/png/txt`以外を拒否する','`gzdeflate`と`strtr`はPlantUML固有のURL表現に必要','`proc_open`へ配列でコマンドを渡しシェル組み立てを避ける','標準入力へUMLソースを送る','標準出力に画像バイナリが返る','子プロセスには15秒の時間制限を設ける','SVGをHTMLに直接挿入せずimgとして表示する']),
 'DiagramRepository':('src/DiagramRepository.php','演習データをJSONから読み、単独取得・検索・ページネーションする。','PHPの配列、`json_decode`、`array_filter`、`array_slice`。','20件のリストのうち、例えば3ページ目の5件を抽出し、本文を取り除いてAPIへ返す。',
   ['IDは数値比較して検索する','入力キーワードはタイトルとテーマに照合する','検索後に`array_values`でインデックスを振り直す','`pages`を`ceil`で計算する','ページ番号を有効範囲へ丸める','一覧には`uml`や`prompt`の長文を含めない','データ編集ではなく読み取り専用の役割に限定する']),
 'PromptGenerator':('src/PromptGenerator.php','テキストの単純なパターン認識からUMLの雛形を返す。AIではない。','正規表現、テーマ分岐、文字列処理。','入力が`Alice -> Bob: Hello`なら、外枠の`@startuml`と`@enduml`を付けてシーケンス図のソースにする。',
   ['テーマによって雛形の構文を分岐する','クラス図は`class Name`の明示的な語を抽出する','状態図は既存の英単語を初期ノードに当てはめる','アクティビティ図は文の区切りをステップとみなす','矢印構文は正規表現で抽出する','自由な日本語の意図をAIで理解する機能はない','生成案は必ず編集して検証する']),
 'api':('public/api.php','HTTPアクションの受付、入力検証、例外処理、JSON応答とバイナリダウンロードを統括する。','HTTPステータス、GET/POST、JSON、ヘッダ、例外と`never`。','`POST?action=render`でJSONを読み、Rendererが実行した結果をHTTPレスポンスへ変換する。',
   ['GETとPOSTの意味を明確に分ける','API成功時と失敗時でHTTPステータスを変える','JSONレスポンスは`Content-Type: application/json`を使う','リモート描画時はバイナリを送らずURLを返す','ローカル描画時はBase64付きJSONを返す','ダウンロード時はattachmentヘッダを付ける','例外を500/422に変換し内部情報を漏らさない','PHP実行ログへ原因を残す']),
 'index':('public/index.php','サーバーサイドで一覧と演習詳細のHTML骨格を生成する。','PHPとHTMLの混在、データ属性、フォーム要素、HTMLエスケープ。','URLに`?id=5`があれば演習詳細のDOMを作り、JavaScriptが動的な内容を取得する。',
   ['タイトルには`escapeHtml`を使う','存在しないIDでは404を返す','一覧・詳細の切替はPHPで行う','エディタはtextareaを最低限のフォールバックにする','画像プレビューはJSが後で生成する','模範解答の表示・非表示を切り替えられる','フォームに明確なaria-labelを与える','外部リンクにはnoopener/noreferrerを検討する']),
 'app.js':('public/assets/app.js','ブラウザUIの状態・イベント・非同期API通信・画像表示・自動保存を担う。','DOM、`fetch`、Promise、`async/await`、`localStorage`、`Blob`と`ObjectURL`。','テキストを編集→650ms待つ→POST描画→形式に応じて`img`または`pre/iframe`へ表示する。',
   ['リクエスト関数はHTTPエラーをJSの例外にする','一覧はPHPのHTMLテーブルへDOM要素を挿入する','文字列は`textContent`で表示する','デバウンスで過剰なAPI呼出を抑える','リクエスト番号で古い画像の反映を防ぐ','ローカルとリモートでは表示方法が変わる','JARがあるときだけBlobダウンロードする','localStorageはユーザーごと・ブラウザごとの保存','Monacoロード失敗時にもtextareaで編集できる']),
 'bootstrap':('src/bootstrap.php','PHPクラスの読み込みと共通HTMLエスケープ関数を提供する。','require_once、関数定義、HTML特殊文字。','index.phpとapi.phpが同じクラスを読み込む。',
   ['require_onceは重複読込を避ける','HTML特殊文字をエスケープしてXSSを防ぐ','関数は画面表示で使い、JSONには使わない']),
 'router':('public/router.php','PHP内蔵開発サーバー用のページ分岐と404処理を行う。','URLのパス、`is_file`、`http_response_code`。','`/`はindex.php、`/api.php`はPHPの実ファイルへ、存在しないURLは404を返す。',
   ['公開ルートはpublicだけである','ルーターはGETパラメータではなくURLのパスを確認する','静的ファイルや実PHPファイルは組込サーバーへ任せる','存在しないパスは404とし、意図せずindexを返さない'])
}

def line_explain(line,lang):
 s=line.strip()
 if not s or s in ('{','}','};',');',')','});','})();', '}',');'):
  return None
 if s.startswith('//') or s.startswith('/*') or s.startswith('*') or s.startswith('#'):
  return 'コメント。処理意図・注意事項を記し、実行結果には直接影響しない。'
 rules=[
 (r'\bdeclare\(strict_types=1\)', 'PHPの暗黙の型変換を制限し、引数の不正な型を早く発見する。'),
 (r'\brequire_once', '別ファイルの定義を1回だけ読み込む。相対パスの基準がどこか確認する。'),
 (r'\bfunction\s+([A-Za-z_][\w]*)', '関数を定義する。呼出側と引数・戻り値の契約を読み取る起点になる。'),
 (r'\b(public|private)\s+function\s+', 'クラスのメソッド定義。可視性、引数、戻り値の型が外部に対する契約となる。'),
 (r'\bclass\s+\w+', 'クラスを定義する。責務に関係するデータとメソッドをまとめる。'),
 (r'\bconst\s+\w+', '定数を定義する。変化しない上限・設定値として使う。'),
 (r'\bthrow new', '異常入力または実行失敗を例外として呼出元へ伝える。API側でHTTPエラーに変換される。'),
 (r'\btry\b', '失敗する可能性のある処理を開始し、失敗時はcatchへ制御が移る。'),
 (r'\bcatch\b', '先行処理が投げた例外を受け、ユーザーに表示するエラーへ変換する。'),
 (r'\bfinally\b', '正常・異常を問わず終了後に実行する後片付け処理。'),
 (r'\bif\s*\(', '条件分岐。条件が真の場合にだけ対応する処理を実行する。'),
 (r'\belse\b', '先の条件が満たされなかったときの分岐。'),
 (r'\bforeach\b', '配列の各要素を順番に取り出して処理する。'),
 (r'\bfor\s*\(', '繰り返し処理。終了条件とインクリメントを必ず確認する。'),
 (r'\breturn\b', '関数の処理を終了し、呼出元に値を返す。'),
 (r'\brespondJson\b', 'HTTPステータスとJSONボディをまとめて出力してリクエストを終了する。'),
 (r'\bjson_decode\b', 'JSON形式のテキストをPHP配列・値へ復元する。'),
 (r'\bjson_encode\b', 'PHP配列・値をJSON文字列に変換する。'),
 (r'\bheader\(', 'HTTP応答ヘッダを設定する。本文より前に出力する必要がある。'),
 (r'\bhttp_response_code\(', 'HTTP応答のステータス番号を設定する。'),
 (r'\bfile_get_contents\(', 'ファイルまたはHTTP本文を文字列として取得する。'),
 (r'\bproc_open\(', '子プロセスを開始する。コマンド引数を配列として安全に渡す。'),
 (r'\bfwrite\(', '標準入力などのストリームへデータを書き込む。'),
 (r'\bstream_get_contents\(', 'ストリームから出力データを読み取る。画像ならバイナリの可能性がある。'),
 (r'\bproc_close\(', '子プロセスの終了状態を回収する。終了コードで成否を判断する。'),
 (r'\bgzdeflate\(', 'ソースをDEFLATE方式で圧縮し、PlantUMLのURLエンコードへ渡す。'),
 (r'\bbase64_encode\(', '画像や圧縮バイト列をテキストとして扱える表現にする。'),
 (r'\bstrtr\(', 'PlantUMLが要求する独自Base64アルファベットへ文字を変換する。'),
 (r'\barray_filter\(', '配列を条件で絞り込む。検索キーワードが一致した要素を残す。'),
 (r'\barray_slice\(', '配列からページに対応する連続部分だけを切り出す。'),
 (r'\barray_map\(', '各要素を整形して新しい配列を作る。一覧の不要フィールドを除去する。'),
 (r'\bpreg_match(_all)?\(', '正規表現で文字列に特定パターンが含まれるか調べる。'),
 (r'\basync\b', '非同期関数。awaitによる中断・再開が可能になる。'),
 (r'\bawait\b', 'Promiseの完了を待って結果を受け取る。画面全体を同期的に停止するわけではない。'),
 (r'\bfetch\(', 'HTTPリクエストを送信する。返るPromiseは応答を示す。'),
 (r'\baddEventListener\(', 'クリックや入力変更などのブラウザイベントにコールバックを登録する。'),
 (r'\.textContent\s*=', '要素の内容を文字列として設定する。HTMLとして解釈しない安全な表示方法。'),
 (r'\.replaceChildren\(', '既存のDOM内容を消し、最新の要素へ置き換える。'),
 (r'\.appendChild\(', 'DOMツリーに新しい要素を追加する。'),
 (r'\.classList\.', 'CSSクラスを変更し、表示・非表示や選択中の見た目を切り替える。'),
 (r'\blocalStorage\.', '同じブラウザ・同じオリジンに編集状態を保存／取得する。サーバーには送らない。'),
 (r'\bsetTimeout\(', '処理の実行を遅らせる。デバウンスやリソース解放に使う。'),
 (r'\bclearTimeout\(', '先に登録したタイマーを取り消して過剰な再描画を防ぐ。'),
 (r'\bcreateObjectURL\(', 'Blobからブラウザ内の一時URLを作成してダウンロードに使う。'),
 (r'\brevokeObjectURL\(', '不要になったオブジェクトURLを解放する。'),
 (r'\bnew Error\(', 'JavaScriptのエラーオブジェクトを生成し、呼出元のcatchへ渡す。'),
 (r'\bdocument\.createElement\(', 'HTML要素を安全なDOM APIとして新規作成する。'),
 (r'\bquerySelector\(', 'CSSセレクタを使ってHTMLの特定要素を取得する。'),
 (r'\bencodeURIComponent\(', 'URLのパラメータに使う文字列をエスケープする。'),
 (r'\bJSON\.stringify\(', 'JavaScriptオブジェクトをHTTPで送れるJSON文字列へ変換する。'),
 (r'\bnew TextDecoder\(', 'ASCIIに限らないUTF-8のバイト列を文字列へ戻す。'),
 ]
 for pattern,explanation in rules:
  if re.search(pattern,s):return explanation
 if s.startswith('<'):
  if re.match(r'<(section|main|header|footer|div|table|textarea|button|input|script|link|body|html|head|a|p|h[1-6]|span)',s):
   return 'HTML要素。タグ名とid/class属性により画面構造やJS操作対象が決まる。'
  return 'HTML構造の一部。開始・終了タグの対応を確認する。'
 if s.startswith('$') or s.startswith('const ') or s.startswith('let '):
  return '変数の代入・初期化。右辺で得た値と、後でどの関数が参照するかを確認する。'
 if '=>' in s or 'function(' in s:return 'コールバック／無名関数。別処理の完了時や配列の各要素に対して実行される。'
 if s.startswith('echo '):return 'HTTPの本文へ出力する。出力前に適切なエスケープがされているか確認する。'
 if '=' in s:return '値または属性を設定する。変数と代入される値の種類を確認する。'
 return '直前の処理に関連する構文。処理順序と周囲のブロックとの関係を確認する。'

for name,(rel,role,prereq,trace,points) in SOURCES.items():
 file=ROOT/rel
 src=file.read_text(encoding='utf-8')
 digest=hashlib.sha256(src.encode()).hexdigest()
 lines=src.splitlines()
 lang='js' if rel.endswith('.js') else 'php' if rel.endswith('.php') else 'text'
 out=[f'# {name} — ソースコード全文と逐次解説', '', f'対象：`{rel}`', f'ソースSHA-256：`{digest}`', '', '## 1. 役割と関連ファイル', '',role,'',f'**前提知識**：{prereq}', '',f'**実行例**：{trace}', '', '## 2. ソースコード全文（省略なし）','',f'```{lang}',src.rstrip('\n'),'```','', '以下では実際のソースの上から下へ進み、原文を小さな範囲に分けて説明する。', '', '## 3. 行・ブロック単位の逐次解説','']
 chunk=9 if name in ('app.js','index','api') else 7
 for start in range(0,len(lines),chunk):
  subset=lines[start:start+chunk]
  out.extend([f'### {start+1}〜{start+len(subset)}行','',f'```{lang}',*subset,'```',''])
  shown=0
  for ln,line in enumerate(subset,start+1):
   explanation=line_explain(line,lang)
   if explanation:
    short=line.strip().replace('`','\\`')
    if len(short)>90:short=short[:87]+'…'
    out.append(f'- **{ln}行目** `{short}`：{explanation}')
    shown+=1
  if shown==0:out.append('この範囲は主に閉じ括弧・空行であり、直前の条件分岐・関数・オブジェクトのスコープを閉じている。')
  out.append('')
 out.extend(['## 4. 実行トレース','','対象の一連の処理を具体的に追う。', '',trace,'',
  'テスト時は、①入力値の型を確認、②関数へ値が渡る箇所を確認、③分岐を予想、④結果・例外・HTTP応答を記録する、という順序で追跡する。','','## 5. このファイルの最重要ポイント',''])
 for i,point in enumerate(points,1):out.append(f'{i}. {point}')
 out.extend(['','## 6. 自習のヒント','',
  'まず上記の全文から関数の入口と出口だけを追い、値の型が変わる位置に印を付ける。次に、自分で1か所だけ変更し、対応する`tests/`の確認が通るか調べる。', '',
  '変更を加えた場合は、この解説に含まれる全文とハッシュも更新する。`python3 scripts/build_walkthroughs.py`で再生成できる。',''])
 (TARGET/(name+'.md')).write_text('\n'.join(out),encoding='utf-8')

names=', '.join(f'`{n}.md`' for n in SOURCES)
(TARGET/'README.md').write_text('# Code Walkthrough — 主要ファイルの完全解説\n\n'+
'対象ファイル：'+names+'。\n\n'+
'各ファイルには概要、元のソース全文、上から下への小ブロック逐次解説、実行トレース、最重要ポイントを収録しています。\n\n'+
'読み方：`api.md` → `Renderer.md` → `app.js.md` → `index.md` → `DiagramRepository.md` → `PromptGenerator.md` の順番を推奨します。\n\n'+
'コード掲載部の内容は実ファイルと完全一致するように再生成しています。ハッシュの一致は`scripts/verify_walkthroughs.py`で確認してください。\n',encoding='utf-8')
print(f'Built {len(SOURCES)} source walkthroughs')
