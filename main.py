from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
import asyncio

from db import DB
from config import TOKEN, ADMIN_ID

db = DB()

bot = Bot(TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Quick command panel
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
panel = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/info"), KeyboardButton(text="/allinfo")],
        [KeyboardButton(text="/pay"), KeyboardButton(text="/reg")],
        [KeyboardButton(text="/admins"), KeyboardButton(text="/addball")],
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer("Добро пожаловать в Республику Д-Стан!", reply_markup=panel)

@dp.message(Command("info"))
async def info(msg: Message):
    target = None
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user.id
    else:
        args = msg.text.split()
        if len(args) >= 2:
            username = args[1].lstrip("@")
            target = db.get_id_by_username(username)
    if target is None:
        target = msg.from_user.id

    user = db.get_user(target)
    if not user:
        await msg.answer("Пользователь не зарегистрирован")
        return

    await msg.answer(f"Баланс: <b>{user['balance']}</b> дэшек")

@dp.message(Command("allinfo"))
async def allinfo(msg: Message):
    users = db.get_all_users()
    text = "💰 <b>Баланс всех граждан:</b>

"
    for u in users:
        text += f"{u['username']} — {u['balance']}
"
    await msg.answer(text)

@dp.message(Command("reg"))
async def reg(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        await msg.answer("Только админ может регистрировать.")
        return
    target = None
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
    else:
        args = msg.text.split()
        if len(args) >= 2:
            username = args[1].lstrip("@")
            target = db.get_user_by_username_raw(username)
    if not target:
        await msg.answer("Не найден пользователь.")
        return

    ok = db.register(target.id, target.username)
    if ok:
        await msg.answer("Пользователь зарегистрирован.")
    else:
        await msg.answer("Пользователь уже был зарегистрирован.")

@dp.message(Command("admins"))
async def admins(msg: Message):
    admins = db.get_admins()
    text = "🛡 <b>Админы:</b>

"
    for a in admins:
        text += f"{a['username']}
"
    await msg.answer(text)

@dp.message(Command("regadmin"))
async def regadmin(msg: Message):
    if msg.from_user.id not in db.get_admin_ids():
        await msg.answer("Только админ может выдавать админку.")
        return

    target = None
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
    else:
        args = msg.text.split()
        if len(args) >= 2:
            username = args[1].lstrip("@")
            target = db.get_user_by_username_raw(username)

    if not target:
        await msg.answer("Не найден пользователь.")
        return

    if not db.user_exists(target.id):
        await msg.answer("Пользователь не зарегистрирован.")
        return

    db.make_admin(target.id)
    await msg.answer("Теперь он админ.")

@dp.message(Command("addball"))
async def addball(msg: Message):
    if msg.from_user.id not in db.get_admin_ids():
        await msg.answer("Ты не админ.")
        return

    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Используй: /addball (ответ или юзернейм) (сумма)")
        return

    target = None
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
        amount = int(args[1])
    else:
        if len(args) < 3:
            await msg.answer("Неверный формат.")
            return
        username = args[1].lstrip("@")
        target = db.get_user_by_username_raw(username)
        amount = int(args[2])

    if not target:
        await msg.answer("Не найден пользователь.")
        return

    if amount < 1:
        await msg.answer("Сумма должна быть ≥ 1")
        return

    if not db.user_exists(target.id):
        await msg.answer("Пользователь не зарегистрирован.")
        return

    db.add_balance(target.id, amount)
    await msg.answer(f"Начислено {amount} дэшек.")

@dp.message(Command("pay"))
async def pay(msg: Message):
    args = msg.text.split()

    target = None
    amount = None

    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
        if len(args) < 2:
            await msg.answer("Укажи сумму: /pay (сумма)")
            return
        amount = int(args[1])
    else:
        if len(args) < 3:
            await msg.answer("Используй: /pay @username сумма")
            return
        username = args[1].lstrip("@")
        target = db.get_user_by_username_raw(username)
        amount = int(args[2])

    if amount < 1:
        await msg.answer("Минимум 1.")
        return

    if not target:
        await msg.answer("Не найден пользователь.")
        return

    if not db.user_exists(target.id) or not db.user_exists(msg.from_user.id):
        await msg.answer("Один из пользователей не зарегистрирован.")
        return

    bal = db.get_user(msg.from_user.id)["balance"]
    if bal < amount:
        await msg.answer("Недостаточно дэшек.")
        return

    db.add_balance(msg.from_user.id, -amount)
    db.add_balance(target.id, amount)

    await msg.answer("Перевод выполнен.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
