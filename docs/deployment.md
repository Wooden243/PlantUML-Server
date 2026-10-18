# 公開とデプロイに関するガイド

## ローカル環境と本番の違い

`php -S`は学習・テスト向け開発サーバーであり、本番の耐障害性・認証・アクセス制御を代替しません。

- Ubuntuサーバー：PHP 8.1+、PHP-FPM、Nginx、Java 17+、Graphvizを用意。
- コードは `/srv/PlantUML-Server/` に配置。Webサーバーの`root`は**必ず** `/srv/PlantUML-Server/public/`。
- JARは`/srv/PlantUML-Server/tools/plantuml.jar`（または `PLANTUML_JAR` 環境変数）から読み込む。
- Nginx側で`client_max_body_size 32k`のように要求サイズを制限、レート制限、HTTPSを有効化。
- PHP-FPMのプロセス実行権限を必要最小限にする。`proc_open`がホスティング会社により禁止されていないか確認する。
- アクセス数が多い場合はCPU・メモリ・タイムアウトの監視、同時Javaプロセス数の上限設定が必要。
- 公開デモであっても不正利用を防ぐ対策なしに広域公開しない。

## Nginx設定の参考

```nginx
server {
    listen 80;
    server_name your-domain.example;
    root /srv/PlantUML-Server/public;
    index index.php;

    location / {
        try_files $uri /index.php?$query_string;
    }
    location ~ \.php$ {
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_pass unix:/run/php/php8.3-fpm.sock;
    }
}
```

この例は**設定概念の説明用**です。PHP-FPMの実バージョン・ソケット、TLS設定、リバースプロキシの安全性要件に合わせて変更してください。`your-domain.example`はプレースホルダーです。

## 将来の改善候補

認証（公開制限）・図の保存DB・レート制限・キャッシュ（同じ図は同じ画像）・Java実行の隔離コンテナ・CI/CD・監視ログ・PlantUMLバージョン固定・依存関係の脆弱性点検。
