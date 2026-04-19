import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

# ==============================
# НАСТРОЙКИ — ЗАПОЛНИ
# ==============================
BOT_TOKEN     = "8014382152:AAGi8WmBc1MO_kPKBCJ0DPIXHQZotlc6ZVU"
CHANNEL_1     = "@trupnoe1"
CHANNEL_2     = "@shizomiu"
SITE_URL      = "https://шизо.мью.рф"
API_BASE      = "https://шизо.мью.рф"
BANNER_PATH   = "banner.jpg"
ADMIN_IDS     = "5888314402"
# ==============================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())

async def check_sub(user_id: int, channel: str) -> bool:
    try:
        m = await bot.get_chat_member(channel, user_id)
        return m.status in ("member", "administrator", "creator")
    except Exception:
        return False

async def both_subs(user_id: int):
    s1 = await check_sub(user_id, CHANNEL_1)
    s2 = await check_sub(user_id, CHANNEL_2)
    return s1, s2

async def api_get(path: str, params: dict = None):
    try:
        async with aiohttp.ClientSession() as s:
            r = await s.get(f"{API_BASE}{path}", params=params, timeout=aiohttp.ClientTimeout(total=5))
            return await r.json()
    except Exception as e:
        logging.error(f"API GET {path}: {e}")
        return None

async def api_post(path: str, data: dict):
    try:
        async with aiohttp.ClientSession() as s:
            r = await s.post(f"{API_BASE}{path}", json=data, timeout=aiohttp.ClientTimeout(total=5))
            return await r.json()
    except Exception as e:
        logging.error(f"API POST {path}: {e}")
        return None

def main_kb(token: str = "") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔐 Верифицироваться", callback_data=f"verify:{token}"),
            InlineKeyboardButton(text="🔗 Привязать аккаунт", callback_data="link"),
        ],
        [
            InlineKeyboardButton(text="👤 Личный кабинет", callback_data="cabinet"),
            InlineKeyboardButton(text="📊 Статус подписки", callback_data="status"),
        ],
        [
            InlineKeyboardButton(text="🎁 Реферальная ссылка", callback_data="ref"),
        ],
        [
            InlineKeyboardButton(text="📢 trupnoe1", url="https://t.me/trupnoe1"),
            InlineKeyboardButton(text="📢 shizomiu", url="https://t.me/shizomiu"),
        ],
    ])

def not_subbed_kb(token, bot_username, s1, s2):
    buttons = []
    if not s1:
        buttons.append([InlineKeyboardButton(text="📢 Подписаться на trupnoe1", url="https://t.me/trupnoe1")])
    if not s2:
        buttons.append([InlineKeyboardButton(text="📢 Подписаться на shizomiu", url="https://t.me/shizomiu")])
    buttons.append([InlineKeyboardButton(
        text="✅ Я подписался — проверить снова",
        url=f"https://t.me/{bot_username}?start={token}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    args = message.text.split()
    token = args[1] if len(args) > 1 else ""
    if token.startswith("ref_"):
        await api_post("/tg_ref_click.php", {"ref_code": token[4:], "tg_user_id": message.from_user.id})
        token = ""

    caption = (
        "<b>Добро пожаловать на шизо.мью!</b>\n\n"
        "Официальный бот сайта. Здесь вы можете:\n\n"
        "🔐 <b>Верифицироваться</b> — получить промокод на 3 дня премиума\n"
        "🔗 <b>Привязать аккаунт</b> — связать TG с аккаунтом сайта\n"
        "👤 <b>Личный кабинет</b> — информация о подписке\n"
        "📊 <b>Статус</b> — проверить активна ли подписка\n"
        "🎁 <b>Рефералы</b> — приглашай друзей, получай скидки\n\n"
        "<i>Для всех функций необходима подписка на наши каналы.</i>"
    )
    try:
        with open(BANNER_PATH, "rb") as f:
            await message.answer_photo(photo=f, caption=caption, parse_mode="HTML", reply_markup=main_kb(token))
    except FileNotFoundError:
        await message.answer(caption, parse_mode="HTML", reply_markup=main_kb(token))

@dp.callback_query(F.data.startswith("verify:"))
async def cb_verify(call: CallbackQuery):
    token = call.data.split(":", 1)[1]
    if not token:
        await call.answer("Используйте кнопку верификации на сайте.", show_alert=True)
        return
    await call.answer("Проверяем подписку...")
    s1, s2 = await both_subs(call.from_user.id)
    if s1 and s2:
        await api_post("/verify_callback.php", {
            "token": token, "tg_user_id": call.from_user.id,
            "tg_username": call.from_user.username or "", "verified": True
        })
        await call.message.answer(
            "✅ <b>Верификация прошла успешно!</b>\n\nВы подписаны на оба канала.\nНажмите кнопку ниже, чтобы получить промокод на <b>3 дня премиума</b>.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🌐 Получить промокод", url=f"{SITE_URL}/verify_success.php?token={token}")
            ]])
        )
    else:
        me = await bot.get_me()
        await call.message.answer(
            "❌ <b>Верификация не пройдена.</b>\n\nНеобходимо подписаться на оба канала:",
            parse_mode="HTML", reply_markup=not_subbed_kb(token, me.username, s1, s2)
        )

@dp.callback_query(F.data == "link")
async def cb_link(call: CallbackQuery):
    await call.answer()
    s1, s2 = await both_subs(call.from_user.id)
    if not (s1 and s2):
        await call.message.answer("⚠️ Для привязки аккаунта подпишитесь на @trupnoe1 и @shizomiu")
        return
    await call.message.answer(
        "🔗 <b>Привязка Telegram к аккаунту</b>\n\nНажмите кнопку — вы будете перенаправлены на сайт.\nВойдите в аккаунт и подтвердите привязку.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔗 Привязать на сайте",
                url=f"{SITE_URL}/link_tg.php?tg_id={call.from_user.id}&tg_name={call.from_user.username or ''}")
        ]])
    )

@dp.callback_query(F.data == "cabinet")
async def cb_cabinet(call: CallbackQuery):
    await call.answer("Загружаем данные...")
    data = await api_get("/tg_user_info.php", {"tg_id": call.from_user.id})
    if not data or not data.get("found"):
        await call.message.answer(
            "👤 <b>Личный кабинет</b>\n\nАккаунт не привязан. Сначала привяжите Telegram к аккаунту на сайте.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔗 Привязать аккаунт", callback_data="link")
            ]])
        )
        return
    premium = "✅ Активна" if data.get("premium") else "❌ Не активна"
    await call.message.answer(
        f"👤 <b>Личный кабинет</b>\n\n"
        f"🙍 Логин: <code>{data.get('login','—')}</code>\n"
        f"💎 Премиум: {premium}\n"
        f"📅 Действует до: <b>{data.get('expires','—')}</b>\n"
        f"🎁 Приглашено друзей: <b>{data.get('refs_count',0)}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🌐 Перейти на сайт", url=SITE_URL)
        ]])
    )

@dp.callback_query(F.data == "status")
async def cb_status(call: CallbackQuery):
    await call.answer("Проверяем...")
    s1, s2 = await both_subs(call.from_user.id)
    data = await api_get("/tg_user_info.php", {"tg_id": call.from_user.id})
    sub1 = "✅" if s1 else "❌"
    sub2 = "✅" if s2 else "❌"
    premium_line = ""
    if data and data.get("found"):
        p = "✅ Активна" if data.get("premium") else "❌ Не активна"
        premium_line = f"\n\n💎 Премиум на сайте: {p}\n📅 До: <b>{data.get('expires','—')}</b>"
    else:
        premium_line = "\n\n💎 Премиум: аккаунт не привязан"
    await call.message.answer(
        f"📊 <b>Статус подписок</b>\n\n{sub1} @trupnoe1\n{sub2} @shizomiu{premium_line}",
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "ref")
async def cb_ref(call: CallbackQuery):
    await call.answer()
    me = await bot.get_me()
    data = await api_get("/tg_ref_info.php", {"tg_id": call.from_user.id})
    refs_count = data.get("refs_count", 0) if data else 0
    ref_code   = data.get("ref_code", f"u{call.from_user.id}") if data else f"u{call.from_user.id}"
    ref_link   = f"https://t.me/{me.username}?start=ref_{ref_code}"
    next_reward = 10 - (refs_count % 10)
    progress    = "▓" * (refs_count % 10) + "░" * (10 - refs_count % 10)
    await call.message.answer(
        f"🎁 <b>Реферальная программа</b>\n\n"
        f"Приглашайте друзей — за каждые <b>10 приглашённых</b> вы получаете скидку <b>30%</b> на премиум!\n\n"
        f"📌 Друг должен перейти по вашей ссылке и подписаться на каналы.\n\n"
        f"👥 Приглашено: <b>{refs_count}</b>\n"
        f"🎯 До следующей скидки: <b>{next_reward}</b> чел.\n"
        f"[{progress}] {refs_count % 10}/10\n\n"
        f"🔗 Ваша ссылка:\n<code>{ref_link}</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="📤 Поделиться", url=f"https://t.me/share/url?url={ref_link}&text=Заходи%20на%20шизо.мью!")
        ]])
    )

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("Использование: /broadcast Текст сообщения")
        return
    data = await api_get("/tg_all_users.php")
    if not data or not data.get("users"):
        await message.answer("Нет пользователей.")
        return
    sent = 0
    for uid in data["users"]:
        try:
            await bot.send_message(uid, text, parse_mode="HTML")
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    await message.answer(f"✅ Отправлено: {sent} пользователям.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
