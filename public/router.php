<?php
declare(strict_types=1);
// Only public/ is exposed. Reject unknown paths rather than serving index content.
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
if ($path === '/' || $path === '/index.php') {
    require __DIR__ . '/index.php';
    return true;
}
$file = __DIR__ . '/' . ltrim((string)$path, '/');
$realFile = realpath($file);
$publicRoot = realpath(__DIR__);
if ($realFile !== false && str_starts_with($realFile, $publicRoot . DIRECTORY_SEPARATOR) && is_file($realFile)) {
    return false;
}
http_response_code(404);
header('Content-Type: text/plain; charset=utf-8');
echo 'Not Found';
