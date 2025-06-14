import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import json
import os

# 🔑 Token, admin ID va majburiy kanal
API_TOKEN = "7518236308:AAEbtvkdQL6BjR6X1RQGIGNulY3SdY2o4xg"
ADMIN_ID = 5088940828
CHANNELS = ["@MyKinoTv_Channel"]

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# 📁 Ma'lumotlarni saqlash uchun JSON
MOVIES_FILE = "movies.json"
if not os.path.exists(MOVIES_FILE):
    with open(MOVIES_FILE, "w") as f:
        json.dump({"movies": [], "channels": CHANNELS}, f)

# 🔑 Tugmalar
def main_menu(is_admin=False):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🎬 Kino olish"))
    if is_admin:
        kb.add(KeyboardButton("➕ Kino qo'shish"))
        kb.add(KeyboardButton("📊 Statistika"))
        kb.add(KeyboardButton("📣 Majburiy obuna"))
    return kb

# 🔑 Majburiy obuna tekshirish
async def check_subscriptions(user_id):
    for ch in load_data()["channels"]:
        member = await bot.get_chat_member(ch, user_id)
        if member.status not in ["member", "creator", "administrator"]:
            return False
    return True

# 🔑 Ma'lumot yuklash
def load_data():
    with open(MOVIES_FILE, "r") as f:
        return json.load(f)

# 🔑 Ma'lumot saqlash
def save_data(data):
    with open(MOVIES_FILE, "w") as f:
        json.dump(data, f)

# 🔑 START
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    data = load_data()
    if user_id not in data.get("users", []):
        data.setdefault("users", []).append(user_id)
        save_data(data)

    if not await check_subscriptions(user_id):
        text = "👋 Salom!\n\nBotdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:"
        btn = InlineKeyboardMarkup(row_width=1)
        for ch in data["channels"]:
            btn.add(InlineKeyboardButton(ch, url=f"https://t.me/{ch.replace('@','')}"))
        btn.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs"))
        await message.answer(text, reply_markup=btn)
    else:
        is_admin = user_id == ADMIN_ID
        await message.answer("Asosiy menyu:", reply_markup=main_menu(is_admin))

# 🔑 Tekshirish tugmasi
@dp.callback_query_handler(lambda c: c.data == "check_subs")
async def check_subs(call: types.CallbackQuery):
    if await check_subscriptions(call.from_user.id):
        is_admin = call.from_user.id == ADMIN_ID
        await call.message.answer("✅ Obuna tekshirildi!", reply_markup=main_menu(is_admin))
    else:
        await call.message.answer("❌ Hali ham barcha kanallarga obuna bo‘lmadingiz!")

# 🔑 Kino qo'shish
@dp.message_handler(lambda m: m.text == "➕ Kino qo'shish")
async def add_movie(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🎬 Iltimos, kino faylini yuboring.")
    dp.register_message_handler(get_movie_file, content_types=types.ContentType.VIDEO, state="get_file")

async def get_movie_file(message: types.Message):
    data = load_data()
    file_id = message.video.file_id
    data["temp_file"] = file_id
    save_data(data)
    await message.answer("📄 Endi kino ma'lumotlarini yuboring.")
    dp.register_message_handler(get_movie_info, state="get_info")

async def get_movie_info(message: types.Message):
    data = load_data()
    info = message.text
    file_id = data.pop("temp_file")
    movies = data["movies"]
    code = len(movies) + 1
    movies.append({"code": code, "file_id": file_id, "info": info})
    save_data(data)
    await message.answer(f"✅ Kino qo'shildi! Kodi: {code}")

# 🔑 Kino olish
@dp.message_handler(lambda m: m.text == "🎬 Kino olish")
async def get_movie(message: types.Message):
    await message.answer("🎥 Kino kodini kiriting:")

@dp.message_handler(lambda m: m.text.isdigit())
async def send_movie(message: types.Message):
    code = int(message.text)
    data = load_data()
    for m in data["movies"]:
        if m["code"] == code:
            await message.answer_video(m["file_id"], caption=m["info"])
            return
    await message.answer("❌ Bunday kodli kino topilmadi!")

# 🔑 Statistika
@dp.message_handler(lambda m: m.text == "📊 Statistika")
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    data = load_data()
    await message.answer(f"👥 Userlar: {len(data.get('users', []))}\n🎬 Kinolar: {len(data['movies'])}")

# 🔑 Majburiy obuna boshqarish
@dp.message_handler(lambda m: m.text == "📣 Majburiy obuna")
async def manage_subs(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("➕ Kanal qo'shish"), KeyboardButton("➖ Kanal o'chirish"))
    kb.add(KeyboardButton("⬅️ Orqaga"))
    await message.answer("Majburiy obunani boshqarish:", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "➕ Kanal qo'shish")
async def add_channel(message: types.Message):
    await message.answer("📣 Kanal usernameni yuboring: @namuna")
    dp.register_message_handler(save_channel, state="add_channel")

async def save_channel(message: types.Message):
    ch = message.text.strip()
    data = load_data()
    if ch not in data["channels"]:
        data["channels"].append(ch)
        save_data(data)
        await message.answer("✅ Kanal qo‘shildi!")
    else:
        await message.answer("❗ Bu kanal avvaldan bor.")

@dp.message_handler(lambda m: m.text == "➖ Kanal o'chirish")
async def remove_channel(message: types.Message):
    await message.answer("❌ O‘chirish uchun kanal usernameni yuboring: @namuna")
    dp.register_message_handler(delete_channel, state="del_channel")

async def delete_channel(message: types.Message):
    ch = message.text.strip()
    data = load_data()
    if ch in data["channels"]:
        data["channels"].remove(ch)
        save_data(data)
        await message.answer("✅ Kanal o‘chirildi.")
    else:
        await message.answer("❗ Bu kanal topilmadi.")

# 🔑 Orqaga
@dp.message_handler(lambda m: m.text == "⬅️ Orqaga")
async def back(message: types.Message):
    is_admin = message.from_user.id == ADMIN_ID
    await message.answer("Asosiy menyu:", reply_markup=main_menu(is_admin))

# --- Ishga tushurish
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
