<?php
declare(strict_types=1);
require_once dirname(__DIR__) . '/src/bootstrap.php';
$passed = 0;
$failed = 0;
function check(bool $condition, string $name): void {
    global $passed, $failed;
    if ($condition) {++$passed; echo "PASS $name\n";}
    else {++$failed; echo "FAIL $name\n";}
}
function throws(callable $fn, string $exception): bool {
    try {$fn();return false;} catch(Throwable $e) {return $e instanceof $exception;}
}
$repo = new DiagramRepository();
$all = $repo->all();
check(count($all) === 20, '20 starter diagrams');
check(count(array_unique(array_column($all, 'id'))) === 20, 'unique numeric IDs');
foreach ($all as $item) {
    check(isset($item['id'], $item['title'], $item['theme'], $item['uml'], $item['prompt']), 'complete data ID ' . $item['id']);
    check(str_contains($item['uml'], '@start') && str_contains($item['uml'], '@end'), 'delimited UML ID ' . $item['id']);
}
check($repo->find(5)['title'] === 'ライフラインの活性化', 'find by ID');
check($repo->find(-1) === null, 'unknown ID');
check($repo->paginate(1)['total'] === 20, 'total pagination count');
check(count($repo->paginate(1)['items']) === 5, 'page size');
check($repo->paginate(4)['items'][0]['id'] === 16, 'fourth page offset');
check($repo->paginate(99)['page'] === 4, 'out-of-range page clamped');
check($repo->paginate(-2)['page'] === 1, 'negative page clamped');
check($repo->paginate(1)['pages'] === 4, 'page count');
check(!array_key_exists('uml', $repo->paginate(1)['items'][0]), 'no source returned in lists');
check($repo->paginate(1, 5, 'クラス図')['total'] >= 2, 'search theme');
check($repo->paginate(1, 5, 'ライフライン')['total'] === 1, 'search title');
check($repo->paginate(1, 5, 'not-present')['total'] === 0, 'search not found');
$renderer = new Renderer('/tmp/nonexistent-plantuml.jar');
check(!$renderer->hasLocalEngine(), 'missing jar detected');
check(throws(fn()=>$renderer->localRender('@startuml\nA -> B\n@enduml', 'svg'),RuntimeException::class), 'missing jar throws');
check($renderer->validateSource('@startuml') === '@startuml', 'source accepted');
check(throws(fn()=>$renderer->validateSource(''),InvalidArgumentException::class), 'empty UML rejected');
check(throws(fn()=>$renderer->validateSource(str_repeat('A',12001)),InvalidArgumentException::class), 'large UML rejected');
check(throws(fn()=>$renderer->validateSource("foo\0bar"),InvalidArgumentException::class), 'NUL rejected');
check(throws(fn()=>$renderer->validateSource("\xFF"),InvalidArgumentException::class), 'invalid utf8 rejected');
check(throws(fn()=>$renderer->validateSource("@startuml\n!include foo\n@enduml"),InvalidArgumentException::class), 'include rejected');
check(throws(fn()=>$renderer->validateSource("!includeurl https://example.com/"),InvalidArgumentException::class), 'includeurl rejected');
check(throws(fn()=>$renderer->validateSource("!include_once file.puml"),InvalidArgumentException::class), 'include_once rejected');
check($renderer->validateFormat('svg') === 'svg', 'svg allowed');
check($renderer->validateFormat('png') === 'png', 'png allowed');
check($renderer->validateFormat('txt') === 'txt', 'txt allowed');
check(throws(fn()=>$renderer->validateFormat('html'),InvalidArgumentException::class), 'html blocked');
$u = $renderer->remoteUrl("@startuml\nAlice -> Bob: Hello\n@enduml", 'svg');
check(str_starts_with($u,'https://www.plantuml.com/plantuml/svg/'), 'remote url prefix');
check((bool)preg_match('~^https://www\.plantuml\.com/plantuml/svg/[0-9A-Za-z_-]+$~',$u), 'safe compressed path');
$encoded = substr($u, strrpos($u,'/')+1);
$canonicalB64 = strtr($encoded,'0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_','ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/');
$decoded = gzinflate(base64_decode($canonicalB64 . str_repeat('=',(4-strlen($canonicalB64)%4)%4),true));
check($decoded === "@startuml\nAlice -> Bob: Hello\n@enduml", 'compression roundtrip');
$gen = new PromptGenerator();
check(str_contains($gen->generate('Alice -> Bob: Hi','シーケンス図'),'Alice -> Bob: Hi'), 'parse explicit arrow');
check(str_contains($gen->generate('class Animal class Dog','クラス図'),'class Dog'), 'parse classes');
check(str_contains($gen->generate('開始。検索。終了','アクティビティ図'),':検索;'), 'parse activity');
check(str_contains($gen->generate('Draft Review','状態図'),'Draft --> Review'), 'parse state');
check(str_contains($gen->generate('機能、性能','マインドマップ'),'** 性能'), 'parse mindmap');
check(throws(fn()=>$gen->generate('','シーケンス図'),InvalidArgumentException::class), 'empty prompt rejected');
check(throws(fn()=>$gen->generate(str_repeat('X',4001),'クラス図'),InvalidArgumentException::class), 'large prompt rejected');
check(escapeHtml('<script>"') === '&lt;script&gt;&quot;', 'HTML escaping');
echo "SUMMARY: $passed passed, $failed failed\n";
exit($failed > 0 ? 1 : 0);
