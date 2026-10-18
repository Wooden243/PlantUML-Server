<?php
declare(strict_types=1);

final class Renderer
{
    private string $jar;
    private string $server;
    private const MAX_SOURCE_BYTES = 12000;

    public function __construct(?string $jar = null, ?string $server = null)
    {
        $this->jar = $jar ?? (getenv('PLANTUML_JAR') ?: dirname(__DIR__) . '/tools/plantuml.jar');
        $this->server = rtrim($server ?? 'https://www.plantuml.com/plantuml', '/');
    }

    public function hasLocalEngine(): bool
    {
        return is_file($this->jar) && is_readable($this->jar);
    }

    public function validateSource(mixed $source): string
    {
        if (!is_string($source) || trim($source) === '') {
            throw new InvalidArgumentException('UMLテキストを入力してください。');
        }
        if (strlen($source) > self::MAX_SOURCE_BYTES) {
            throw new InvalidArgumentException('UMLは12,000バイト以内にしてください。');
        }
        if (str_contains($source, "\0") || preg_match('//u', $source) !== 1) {
            throw new InvalidArgumentException('有効なUTF-8テキストを入力してください。');
        }
        // Forbid all preprocessor directives: includes and advanced macros can access resources.
        if (preg_match('/^\s*!/m', $source)) {
            throw new InvalidArgumentException('このサービスでは !include などの外部読み込み・拡張命令は使えません。');
        }
        return $source;
    }

    public function validateFormat(mixed $format): string
    {
        if (!is_string($format) || !in_array($format, ['svg', 'png', 'txt'], true)) {
            throw new InvalidArgumentException('出力形式はsvg/png/txtから指定してください。');
        }
        return $format;
    }

    public function encode(string $source): string
    {
        // PlantUML uses raw DEFLATE with a custom Base64 alphabet.
        $standard = rtrim(base64_encode(gzdeflate($source, 9)), '=');
        return strtr($standard, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/', '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_');
    }

    public function remoteUrl(string $source, string $format): string
    {
        return $this->server . '/' . $this->validateFormat($format) . '/' . $this->encode($this->validateSource($source));
    }

    /** @return array{format: string, contentType: string, bytes: string} */
    public function localRender(string $source, string $format): array
    {
        $source = $this->validateSource($source);
        $format = $this->validateFormat($format);
        if (!$this->hasLocalEngine()) {
            throw new RuntimeException('PlantUML JARがありません。READMEの導入手順を確認してください。');
        }
        $cmd = ['timeout', '15s', 'java', '-Djava.awt.headless=true', '-jar', $this->jar, '-pipe', '-t' . $format];
        $pipes = [];
        $environment = ['PLANTUML_SECURITY_PROFILE' => 'SANDBOX', 'PATH' => (getenv('PATH') ?: '/usr/bin:/bin')];
        $process = proc_open($cmd, [0 => ['pipe','r'],1 => ['pipe','w'],2 => ['pipe','w']], $pipes, dirname(__DIR__), $environment);
        if (!is_resource($process)) {
            throw new RuntimeException('Javaエンジンの起動に失敗しました。');
        }
        fwrite($pipes[0], $source);
        fclose($pipes[0]);
        $bytes = stream_get_contents($pipes[1]);
        fclose($pipes[1]);
        $errors = stream_get_contents($pipes[2]);
        fclose($pipes[2]);
        $code = proc_close($process);
        if ($code !== 0 || $bytes === false || strlen($bytes) > 5000000) {
            throw new RuntimeException('図の生成に失敗しました（終了コード ' . $code . '）。' . substr(trim((string)$errors), 0, 250));
        }
        $types = ['svg' => 'image/svg+xml', 'png' => 'image/png', 'txt' => 'text/plain; charset=utf-8'];
        return ['format' => $format, 'contentType' => $types[$format], 'bytes' => $bytes];
    }
}
