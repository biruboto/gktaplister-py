<?php
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(["error" => "Method not allowed"]);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
if (!is_array($input)) {
    http_response_code(400);
    echo json_encode(["error" => "Invalid JSON"]);
    exit;
}

$side = $input['side'] ?? '';
$action = $input['action'] ?? '';

$targets = [
    'red' => [
        'ssh_target' => getenv('GK_RED_SSH_TARGET') ?: 'taplister-red',
        'service' => 'gk-taplister-red.service',
    ],
    'blue' => [
        'ssh_target' => getenv('GK_BLUE_SSH_TARGET') ?: 'taplister-blue',
        'service' => 'gk-taplister-blue.service',
    ],
];

if (!isset($targets[$side])) {
    http_response_code(400);
    echo json_encode(["error" => "Unknown kiosk side"]);
    exit;
}

$service = $targets[$side]['service'];
$sshTarget = $targets[$side]['ssh_target'];

$remoteCommands = [
    'restart' => "sudo systemctl restart {$service}",
    'reboot' => "sudo systemctl reboot",
];

if (!isset($remoteCommands[$action])) {
    http_response_code(400);
    echo json_encode(["error" => "Unknown control action"]);
    exit;
}

$sshBin = trim((string) shell_exec('command -v ssh 2>/dev/null'));
if ($sshBin === '') {
    http_response_code(500);
    echo json_encode(["error" => "ssh binary not available on host"]);
    exit;
}

$sshTargetArg = escapeshellarg($sshTarget);
$remoteCommandArg = escapeshellarg($remoteCommands[$action]);
$command = "{$sshBin} -o BatchMode=yes -o ConnectTimeout=5 {$sshTargetArg} {$remoteCommandArg} 2>&1";

$output = [];
$exitCode = 0;
exec($command, $output, $exitCode);

if ($exitCode !== 0) {
    http_response_code(500);
    echo json_encode([
        "error" => "Remote control failed",
        "details" => trim(implode("\n", $output)) ?: "ssh returned exit code {$exitCode}",
    ]);
    exit;
}

echo json_encode([
    "status" => "ok",
    "message" => ucfirst($action) . " requested for {$side} kiosk.",
]);
exit;
?>
