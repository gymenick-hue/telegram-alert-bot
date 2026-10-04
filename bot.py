import os
import asyncio
import logging

from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher
from aiogram.types import Message


TOKEN = os.environ["BOT_TOKEN"]
PORT = int(os.environ.get("PORT", "10000"))

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()

subscribers = set()

# Поточні активні загрози Кіровоградської області
last_threats = set()


# --------------------------------------------------
# TELEGRAM
# --------------------------------------------------

@dp.message()
async def handle_message(message: Message):

    if message.text and message.text.startswith("/start"):
        subscribers.add(message.chat.id)

        await message.answer(
            "✅ Бот працює!\n\n"
            "Ви підписані на сповіщення для Кіровоградської області.\n\n"
            "🚨 Повітряна тривога\n"
            "🛩️ БПЛА\n"
            "🚀 Ракети\n"
            "💥 Балістика\n"
            "✈️ Авіація\n"
            "💣 КАБ\n"
            "🟢 Відбій"
        )

    elif message.text and message.text.startswith("/test"):
        subscribers.add(message.chat.id)

        await message.answer(
            "🧪 ТЕСТОВЕ ПОВІДОМЛЕННЯ\n\n"
            "🚨 Повітряна тривога\n"
            "🛩️ БПЛА\n"
            "🚀 Ракета\n"
            "💥 Балістика\n"
            "✈️ Авіація\n"
            "💣 КАБ\n"
            "🟢 Відбій"
        )


# --------------------------------------------------
# НАДСИЛАННЯ
# --------------------------------------------------

async def send_to_all(text):
    for chat_id in list(subscribers):
        try:
            await bot.send_message(chat_id, text)
        except Exception:
            logging.exception("Помилка надсилання повідомлення")


# --------------------------------------------------
# ВИЗНАЧЕННЯ ТИПУ ЗАГРОЗИ
# --------------------------------------------------

def detect_threats(oblast):

    threats = set()

    reasons = oblast.get("reasons", [])

    for reason in reasons:

        text = str(reason).lower()

        if "дрон" in text or "бпла" in text:
            threats.add("drone")

        if "ракет" in text:
            threats.add("missile")

        if "баліст" in text:
            threats.add("ballistic")

        if "авіац" in text or "авіаційн" in text:
            threats.add("aviation")

        if "каб" in text:
            threats.add("kab")

    # Якщо область має тривогу, але причина не вказана
    # — все одно фіксуємо загальну повітряну тривогу.
   
