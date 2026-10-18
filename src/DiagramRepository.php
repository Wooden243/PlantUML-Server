<?php
declare(strict_types=1);

final class DiagramRepository
{
    /** @return array<int, array<string, mixed>> */
    public function all(): array
    {
        $path = dirname(__DIR__) . '/storage/examples.json';
        $items = json_decode((string) file_get_contents($path), true, 512, JSON_THROW_ON_ERROR);
        if (!is_array($items)) {
            throw new RuntimeException('Example data is not an array.');
        }
        return $items;
    }

    /** @return array<string,mixed>|null */
    public function find(int $id): ?array
    {
        foreach ($this->all() as $item) {
            if ($item['id'] === $id) {
                return $item;
            }
        }
        return null;
    }

    /** @return array{items: array<int, array<string, mixed>>, total: int, page: int, pages: int} */
    public function paginate(int $page, int $perPage = 5, string $keyword = ''): array
    {
        $keyword = trim($keyword);
        $all = array_values(array_filter($this->all(), static function (array $item) use ($keyword): bool {
            if ($keyword === '') {
                return true;
            }
            return stripos(($item['title'] . ' ' . $item['theme']), $keyword) !== false;
        }));
        $total = count($all);
        $pages = max(1, (int) ceil($total / $perPage));
        $page = min(max(1, $page), $pages);
        $items = array_slice($all, ($page - 1) * $perPage, $perPage);
        $items = array_map(static function (array $item): array {
            unset($item['uml'], $item['prompt']);
            return $item;
        }, $items);
        return compact('items', 'total', 'page', 'pages');
    }
}
