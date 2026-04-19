<?php
// verify_success.php — страница куда бот редиректит после успешной верификации

session_start();

$host     = "localhost";
$db       = "u3458519_sh1zo";
$user     = "u3458519_s";
$password = "shizoid228@@@";

$pdo = new PDO("mysql:host=$host;dbname=$db;charset=utf8", $user, $password);

$token = $_GET['token'] ?? '';
$promo = null;

if ($token) {
    $stmt = $pdo->prepare("
        SELECT promo_code FROM verifications
        WHERE token = ? AND verified = 1
    ");
    $stmt->execute([$token]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    $promo = $row['promo_code'] ?? null;
}
?>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Верификация — шизо.мью</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0f0f0f;
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .card {
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 16px;
            padding: 40px;
            text-align: center;
            max-width: 420px;
            width: 90%;
        }
        .icon { font-size: 48px; margin-bottom: 16px; }
        h1 { font-size: 22px; margin-bottom: 10px; }
        p { color: #888; font-size: 15px; line-height: 1.5; margin-bottom: 20px; }
        .promo-box {
            background: #111;
            border: 1px dashed #444;
            border-radius: 10px;
            padding: 16px;
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 4px;
            color: #fff;
            margin-bottom: 24px;
            user-select: all;
        }
        .btn {
            display: inline-block;
            background: #fff;
            color: #000;
            padding: 12px 28px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            font-size: 15px;
            transition: opacity .2s;
        }
        .btn:hover { opacity: 0.85; }
        .error { color: #e55; }
    </style>
</head>
<body>
<div class="card">
    <?php if ($promo): ?>
        <div class="icon">🎉</div>
        <h1>Верификация пройдена!</h1>
        <p>Ваш промокод на премиум-подписку на <b>3 дня</b>:</p>
        <div class="promo-box"><?= htmlspecialchars($promo) ?></div>
        <p>Введите его на странице оформления подписки.</p>
        <a href="https://шизо.мью" class="btn">На главную</a>
    <?php else: ?>
        <div class="icon">❌</div>
        <h1 class="error">Что-то пошло не так</h1>
        <p>Промокод не найден. Возможно, ссылка устарела. Попробуйте пройти верификацию заново.</p>
        <a href="https://шизо.мью" class="btn">На сайт</a>
    <?php endif; ?>
</div>
</body>
</html>
