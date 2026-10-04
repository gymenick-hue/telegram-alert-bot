import os
import asyncio
import logging

from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher
from aiogram.types import Message


# =========================
# НАЛАШТУВАННЯ
# =========================

BOT_TOKEN = os.environ["BOT_TOKEN"]
BALLISTIC_BOT_TOKEN = os.environ["BALLISTIC_BOT_TOKEN"]

PORT = int(os.environ.get("PORT", "10000"))

BASE_URL = "https://telegram-alert-bot-1-yo3t.onrender.com"

DRONE_WEBHOOK_PATH = "/telegram-webhook"
BALLISTIC_WEBHOOK_PATH = "/ballistic-webhook"

DRONE_WEBHOOK_URL = BASE_URL + DRONE_WEBHOOK_PATH
BALLISTIC_WEBHOOK_URL = BASE_URL + BALLISTIC_WEBHOOK_PATH

NEPTUN_URL = "https://neptun.in.ua/api/v1/alerts"


logging.basicConfig(level=logging.INFO)


# =========================
# БОТИ
# =========================

drone_bot = Bot(BOT_TOKEN)
ballistic_bot = Bot(BALLISTIC_BOT_TOKEN)

drone_dp = Dispatcher()
ballistic_dp = Dispatcher()

drone_subscribers = set()
ballistic_subscribers = set()

drone_active = False
ballistic_active = False


# =========================
# ПЕРШИЙ БОТ — БПЛА
# =========================

@drone_dp.message()
async def handle_drone_message(message: Message):

    if message.text and message.text.startswith("/start"):

        drone_subscribers.add(message.chat.id)

        await message.answer(
            "✅ Бот працює!\n\n"
            "Підписка на БПЛА:\n"
            "📍 Кропивницький\n"
            "📍 Кропивницький район\n\n"
            "🛩️ Тільки БПЛА.\n"
            "🔕 Відбій не надсилається."
        )

    elif message.text and message.text.startswith("/test"):

        drone_subscribers.add(message.chat.id)

        await message.answer(
            "🧪 ТЕСТ БПЛА\n\n"
            "🛩️ БПЛА!\n\n"
            "Кропивницький / Кропивницький район."
        )


# =========================
# ДРУГИЙ БОТ — БАЛІСТИКА
# =========================

@ballistic_dp.message()
async def handle_ballistic_message(message: Message):

    if message.text and message.text.startswith("/start"):

        ballistic_subscribers.add(message.chat.id)

        await message.answer(
            "✅ Бот працює!\n\n"
            "Підписка на балістику:\n"
            "📍 Кропивницький\n"
            "📍 Кропивницький район\n\n"
            "💥 Тільки балістика.\n"
            "🔕 Відбій не надсилається."
        )

    elif message.text and message.text.startswith("/test"):

        ballistic_subscribers.add(message.chat.id)

        await message.answer(
            "🧪 ТЕСТ БАЛІСТИКИ\n\n"
            "💥 БАЛІСТИЧНА ЗАГРОЗА!\n\n"
            "Кропивницький / Кропивниць
