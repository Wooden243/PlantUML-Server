<?php
declare(strict_types=1);

/** Deterministic practice helper; not an AI model. */
final class PromptGenerator
{
    public function generate(mixed $description, mixed $theme): string
    {
        if (!is_string($description) || trim($description) === '' || strlen($description) > 4000) {
            throw new InvalidArgumentException('作成したい図の説明を1〜4,000バイトで入力してください。');
        }
        $theme = is_string($theme) ? $theme : 'シーケンス図';
        if ($theme === 'クラス図') {
            preg_match_all('/(?:class|クラス)\s*[:：]?\s*([A-Za-z][A-Za-z0-9_]*)/iu', $description, $hits);
            $names = array_unique($hits[1]);
            if (!$names) $names = ['Customer', 'Order'];
            $lines = ['@startuml'];
            foreach (array_slice($names, 0, 12) as $name) $lines[] = 'class ' . $name;
            $lines[] = '@enduml';
            return implode("\n", $lines);
        }
        if ($theme === '状態図') {
            $names = $this->tokens($description);
            $a = $names[0] ?? 'Draft'; $b = $names[1] ?? 'Review';
            return "@startuml\n[*] --> $a\n$a --> $b\n$b --> [*]\n@enduml";
        }
        if ($theme === 'アクティビティ図') {
            $steps = preg_split('/[。\n;]+/u', trim($description)) ?: [];
            $lines = ['@startuml', 'start'];
            foreach (array_slice($steps, 0, 8) as $step) {
                $step = str_replace([':', ';'], ' ', trim($step));
                if ($step !== '') $lines[] = ':' . substr($step, 0, 70) . ';';
            }
            $lines[] = 'stop'; $lines[] = '@enduml';
            return implode("\n", $lines);
        }
        if ($theme === 'マインドマップ') {
            $steps = preg_split('/[、,。\n]+/u', trim($description)) ?: [];
            $lines = ['@startmindmap', '* Topic'];
            foreach (array_slice($steps, 0, 10) as $step) {
                $step = str_replace(["\r", "\n"], ' ', trim($step));
                if ($step !== '') $lines[] = '** ' . substr($step, 0, 80);
            }
            $lines[] = '@endmindmap';
            return implode("\n", $lines);
        }
        // Sequence diagrams: extract explicit 'A -> B: message' lines or create a starter.
        preg_match_all('/^\s*([A-Za-z][A-Za-z0-9_]*)\s*(-+>|-->|->>)\s*([A-Za-z][A-Za-z0-9_]*)\s*:\s*([^\r\n]+)/m', $description, $matches, PREG_SET_ORDER);
        if ($matches) {
            $lines = ['@startuml'];
            foreach (array_slice($matches, 0, 15) as $match) {
                $lines[] = $match[1] . ' ' . $match[2] . ' ' . $match[3] . ': ' . str_replace(['\r','\n'], ' ', trim($match[4]));
            }
            $lines[] = '@enduml';
            return implode("\n", $lines);
        }
        $names = $this->tokens($description);
        $a = $names[0] ?? 'Alice'; $b = $names[1] ?? 'Bob';
        if ($a === $b) $b = 'System';
        return "@startuml\n$a -> $b: request\n$b --> $a: response\n@enduml";
    }

    /** @return string[] */
    private function tokens(string $text): array
    {
        preg_match_all('/\b[A-Z][A-Za-z0-9_]{2,}\b/', $text, $matches);
        return array_values(array_unique(array_slice($matches[0], 0, 2)));
    }
}
