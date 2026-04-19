<?php
// verify_callback.php — бот сюда отправляет результат верификации

$host     = "localhost";
$db       = "u3458519_sh1zo";
$user     = "u3458519_s";
$password = "shizoid228@@@";

$pdo = new PDO("mysql:host=$host;dbname=$db;charset=utf8", $user, $password);
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$input = json_decode(file_get_contents("php://input"), true);

if (!$input || empty($input['token'])) {
    http_response_code(400);
    echo json_encode(["error" => "Неверный запрос"]);
    exit;
}

$token     = $input['token'];
$tg_id     = $input['tg_user_id'] ?? null;
$tg_name   = $input['tg_username'] ?? '';
$verified  = $input['verified'] ?? false;

if (!$verified) {
    echo json_encode(["ok" => false]);
    exit;
}

// Проверяем токен и срок действия
$stmt = $pdo->prepare("
    SELECT site_user_id FROM verifications
    WHERE token = ? AND expires_at > NOW() AND verified = 0
");
$stmt->execute([$token]);
$row = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$row) {
    http_response_code(400);
    echo json_encode(["error" => "Токен недействителен или истёк"]);
    exit;
}

$site_user_id = $row['site_user_id'];

// Генерируем промокод
$promo = strtoupper(bin2hex(random_bytes(4))); // например: A3F91C2B

// Обновляем запись — верифицирован
$stmt = $pdo->prepare("
    UPDATE verifications
    SET verified = 1, tg_user_id = ?, tg_username = ?, promo_code = ?, verified_at = NOW()
    WHERE token = ?
");
$stmt->execute([$tg_id, $tg_name, $promo, $token]);

echo json_encode(["ok" => true]);
