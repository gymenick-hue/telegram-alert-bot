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
            "Ви підписані на БПЛА для:\n"
            "📍 м. Кропивницький\n"
            "📍 Кропивницький район\n\n"
            "🛩️ Тільки дронова загроза.\n"
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
            "Ви підписані на балістичну загрозу для:\n"
            "📍 м. Кропивницький\n"
            "📍 Кропивницький район\n\n"
            "💥 Тільки балістична загроза.\n"
            "🔕 Відбій не надсилається."
        )

    elif message.text and message.text.startswith("/test"):
        ballistic_subscribers.add(message.chat.id)

        await message.answer(
            "🧪 ТЕСТ БАЛІСТИКИ\n\n"
            "💥 БАЛІСТИЧНА ЗАГРОЗА!\n\n"
            "Кропивницький / Кропивницький район."
        )


# =========================
# НАДСИЛАННЯ
# =========================

async def send_drone(text):
    for chat_id in list(drone_subscribers):
        try:
            await drone_bot.send_message(chat_id, text)
        except Exception:
            logging.exception("Помилка надсилання БПЛА")


async def send_ballistic(text):
    for chat_id in list(ballistic_subscribers):
        try:
            await ballistic_bot.send_message(chat_id, text)
        except Exception:
            logging.exception("Помилка надсилання балістики")


# =========================
# ПОШУК ПОТРІБНОЇ ТЕРИТОРІЇ
# =========================

def is_target(item):
    name = str(item.get("name", "")).lower()
    key = str(item.get("key", "")).lower()
    oblast = str(item.get("oblast", "")).lower()

    text = f"{name} {key} {oblast}"

    if "кропивницький район" in text:
        return True

    if "кропивницький" in text and "район" not in text:
        return True

    return False


# =========================
# ПЕРЕВІРКА БПЛА
# =========================

def is_drone_threat(item):
    reasons = item.get("reasons", [])

    for reason in reasons:
        text = str(reason).lower()

        if "дрон" in text or "бпла" in text:
            return True

    return False


# =========================
# ПЕРЕВІРКА БАЛІСТИКИ
# =========================

def is_ballistic_threat(item):
    reasons = item.get("reasons", [])

    for reason in reasons:
        text = str(reason).lower()

        if "баліст" in text:
            return True

    return False


# =========================
# ПЕРЕВІРКА NEPTUN
# =========================

async def check_alerts():
    global drone_active
    global ballistic_active

    await asyncio.sleep(5)

    async with ClientSession() as session:

        while True:
            try:
                async with session.get(
                    NEPTUN_URL,
                    timeout=10
                ) as response:

                    alerts = await response.json()

                current_drone = False
                current_ballistic = False

                # Райони
                for item in alerts.get("raions", []):

                    if not is_target(item):
                        continue

                    if is_drone_threat(item):
                        current_drone = True

                    if is_ballistic_threat(item):
                        current_ballistic = True

                # Інші записи
                for item in alerts.get("oblasts", []):

                    if not is_target(item):
                        continue

                    if is_drone_threat(item):
                        current_drone = True

                    if is_ballistic_threat(item):
                        current_ballistic = True

                # =========================
                # БПЛА
                # =========================

                if current_drone and not drone_active:

                    await send_drone(
                        "🛩️ БПЛА!\n\n"
                        "Кропивницький / Кропивницький район.\n"
                        "Будьте уважні та стежте за офіційними повідомленнями."
                    )

                # =========================
                # БАЛІСТИКА
                # =========================

                if current_ballistic and not ballistic_active:

                    await send_ballistic(
                        "💥 БАЛІСТИЧНА ЗАГРОЗА!\n\n"
                        "Кропивницький / Кропивницький район.\n"
                        "НЕГАЙНО В УКРИТТЯ!"
                    )

                # Відбій НЕ надсилаємо
                drone_active = current_drone
                ballistic_active = current_ballistic

                logging.info(
                    "Кропивницький — БПЛА: %s | Балістика: %s",
                    current_drone,
                    current_ballistic
                )

            except Exception:
                logging.exception("Помилка перевірки NEPTUN")

            await asyncio.sleep(5)


# =========================
# WEBHOOK БПЛА
# =========================

async def drone_webhook(request):
    try:
        data = await request.json()

        await drone_dp.feed_webhook_update(
            drone_bot,
            data
        )

        return web.Response(text="OK")

    except Exception:
        logging.exception("Помилка webhook БПЛА")
        return web.Response(
            status=500,
            text="ERROR"
        )


# =========================
# WEBHOOK БАЛІСТИКИ
# =========================

async def ballistic_webhook(request):
    try:
        data = await request.json()

        await ballistic_dp.feed_webhook_update(
            ballistic_bot,
            data
        )

        return web.Response(text="OK")

    except Exception:
        logging.exception("Помилка webhook балістики")
        return web.Response(
            status=500,
            text="ERROR"
        )


# =========================
# HEALTH
# =========================

async def health(request):
    return web.Response(text="Bot is running")


# =========================
# STARTUP
# =========================

async def startup(app):

    logging.info("Запуск двох ботів...")

    await drone_bot.set_webhook(
        url=DRONE_WEBHOOK_URL,
        allowed_updates=["message"]
    )

    logging.info(
        "Webhook БПЛА: %s",
        DRONE_WEBHOOK_URL
    )

    await ballistic_bot.set_webhook(
        url=BALLISTIC_WEBHOOK_URL,
        allowed_updates=["message"]
    )

    logging.info(
        "Webhook балістики: %s",
        BALLISTIC_WEBHOOK_URL
    )

    app["alert_task"] = asyncio.create_task(
        check_alerts()
    )


# =========================
# CLEANUP
# =========================

async def cleanup(app):

    app["alert_task
