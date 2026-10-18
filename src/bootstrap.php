<?php
declare(strict_types=1);
require_once __DIR__ . '/DiagramRepository.php';
require_once __DIR__ . '/Renderer.php';
require_once __DIR__ . '/PromptGenerator.php';
function escapeHtml(string $value): string
{
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}
