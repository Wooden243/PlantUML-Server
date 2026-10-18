<?php
declare(strict_types=1);
require_once dirname(__DIR__).'/src/bootstrap.php';
$dir=sys_get_temp_dir().'/pu-mock-'.bin2hex(random_bytes(4));
mkdir($dir);
$jar=$dir.'/plantuml.jar';
file_put_contents($jar,'dummy');
$java=$dir.'/java';
file_put_contents($java, "#!/bin/sh\ncat >/dev/null\nprintf '<svg xmlns=\"http://www.w3.org/2000/svg\"></svg>'\n");
chmod($java,0755);
$oldPath=getenv('PATH');
putenv('PATH='.$dir.':'.$oldPath);
try {
    $renderer=new Renderer($jar);
    $result=$renderer->localRender("@startuml\nAlice -> Bob\n@enduml",'svg');
    if ($result['contentType'] !== 'image/svg+xml' || !str_contains($result['bytes'], '<svg')) {
        throw new RuntimeException('Unexpected mock output');
    }
    echo "PASS local subprocess branch using mock Java executable (not real PlantUML rendering)\n";
} finally {
    putenv('PATH='.$oldPath);
    unlink($java);unlink($jar);rmdir($dir);
}
