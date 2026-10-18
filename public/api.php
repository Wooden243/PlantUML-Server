<?php
declare(strict_types=1);
require_once dirname(__DIR__) . '/src/bootstrap.php';
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');
header('Referrer-Policy: no-referrer');
header('X-Frame-Options: DENY');

function respondJson(array $data, int $status = 200): never
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
    exit;
}

try {
    $action = $_GET['action'] ?? '';
    $repo = new DiagramRepository();
    $renderer = new Renderer();
    if ($action === 'list' && $_SERVER['REQUEST_METHOD'] === 'GET') {
        respondJson($repo->paginate((int)($_GET['page'] ?? 1), 5, (string)($_GET['q'] ?? '')));
    }
    if ($action === 'detail' && $_SERVER['REQUEST_METHOD'] === 'GET') {
        $id = filter_var($_GET['id'] ?? null, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
        if ($id === false || $id === null) throw new InvalidArgumentException('IDを指定してください。');
        $item = $repo->find($id);
        if (!$item) respondJson(['error' => '図が見つかりません。'], 404);
        respondJson($item);
    }
    if ($action === 'status' && $_SERVER['REQUEST_METHOD'] === 'GET') {
        respondJson(['renderer' => $renderer->hasLocalEngine() ? 'local' : 'remote', 'hasLocalEngine' => $renderer->hasLocalEngine()]);
    }
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        respondJson(['error' => '未対応のアクションです。'], 404);
    }
    $body = file_get_contents('php://input');
    if ($body === false || strlen($body) > 20000) throw new InvalidArgumentException('リクエストが大きすぎます。');
    $data = json_decode($body, true, 32, JSON_THROW_ON_ERROR);
    if (!is_array($data)) throw new InvalidArgumentException('JSON形式の入力が必要です。');

    if ($action === 'generate') {
        $uml = (new PromptGenerator())->generate($data['description'] ?? null, $data['theme'] ?? 'シーケンス図');
        respondJson(['uml' => $uml, 'generator' => 'rule-based']);
    }
    if ($action === 'render' || $action === 'download') {
        $uml = $renderer->validateSource($data['uml'] ?? null);
        $format = $renderer->validateFormat($data['format'] ?? 'svg');
        if ($renderer->hasLocalEngine()) {
            $result = $renderer->localRender($uml, $format);
            if ($action === 'download') {
                header('Content-Type: ' . $result['contentType']);
                header('Content-Disposition: attachment; filename="diagram.' . $format . '"');
                header('Content-Security-Policy: sandbox');
                echo $result['bytes'];
                exit;
            }
            respondJson([
                'mode' => 'local',
                'format' => $format,
                'mime' => $result['contentType'],
                'base64' => base64_encode($result['bytes']),
            ]);
        }
        if ($action === 'download') {
            respondJson(['error' => 'サーバー側でのファイルダウンロードにはPlantUML JARが必要です。', 'url' => $renderer->remoteUrl($uml, $format)], 503);
        }
        respondJson(['mode' => 'remote', 'format' => $format, 'url' => $renderer->remoteUrl($uml, $format)]);
    }
    respondJson(['error' => '未対応のアクションです。'], 404);
} catch (JsonException | InvalidArgumentException $error) {
    respondJson(['error' => $error->getMessage()], 422);
} catch (Throwable $error) {
    error_log('PlantUML server error: ' . $error->getMessage());
    respondJson(['error' => 'サーバー側でエラーが発生しました。ログを確認してください。'], 500);
}
