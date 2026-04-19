<?php
// verify_start.php — генерирует токен и редиректит в бота
// Вызывается с сайта когда юзер нажимает "Верифицироваться"

session_start();

$host     = "localhost";
$db       = "u3458519_sh1zo";   // заполни
$user     = "u3458519_s";    // заполни
$password = "shizoid228@@@";          // заполни

$pdo = new PDO("mysql:host=$host;dbname=$db;charset=utf8", $user, $password);
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

// ID пользователя сайта — берём из сессии (подстрой под свою систему)
$site_user_id = $_SESSION['user_id'] ?? null;

if (!$site_user_id) {
    http_response_code(401);
    echo json_encode(["error" => "Необходима авторизация на сайте"]);
    exit;
}

// Проверяем — не верифицировался ли уже
$stmt = $pdo->prepare("SELECT verified FROM verifications WHERE site_user_id = ?");
$stmt->execute([$site_user_id]);
$row = $stmt->fetch(PDO::FETCH_ASSOC);

if ($row && $row['verified']) {
    echo json_encode(["error" => "already_verified"]);
    exit;
}

// Генерируем уникальный токен
$token = bin2hex(random_bytes(16));
$expires_at = date('Y-m-d H:i:s', time() + 300); // живёт 5 минут

// Сохраняем токен в БД
$stmt = $pdo->prepare("
    INSERT INTO verifications (site_user_id, token, expires_at, verified)
    VALUES (?, ?, ?, 0)
    ON DUPLICATE KEY UPDATE token = VALUES(token), expires_at = VALUES(expires_at), verified = 0
");
$stmt->execute([$site_user_id, $token, $expires_at]);

// Ссылка на бота с токеном
$bot_username = "shizomiu_bot"; // например shizomiu_bot — без @
$bot_url = "https://t.me/{$bot_username}?start={$token}";

echo json_encode(["bot_url" => $bot_url]);
