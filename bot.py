import os
import asyncio
import logging

from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher
from aiogram.types import Message


TOKEN = os.environ["BOT_TOKEN"]
PORT = int(os.environ.get("PORT", "10000"))

BASE_URL = "https://telegram-alert-bot-1-yo3t.onrender.com"
WEBHOOK_PATH = "/telegram-webhook"
WEBHOOK_URL = BASE_URL + WEBHOOK_PATH

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()

subscribers = set()
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
            logging.exception("Помилка надсилання")


# --------------------------------------------------
# ВИЗНАЧЕННЯ ЗАГРОЗ
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

        if "авіац" in text:
            threats.add("aviation")

        if "каб" in text:
            threats.add("kab")

    if oblast.get("level") == "red":
        threats.add("air_raid")

    return threats


# --------------------------------------------------
# NEPTUN
# --------------------------------------------------

async def check_alerts():

    global last_threats

    await asyncio.sleep(5)

    async with ClientSession() as session:

        while True:

            try:

                async with session.get(
                    "https://neptun.in.ua/api/v1/alerts",
                    timeout=10
                ) as response:

                    alerts = await response.json()

                oblasts = alerts.get("oblasts", [])

                kirovohrad = None

                for oblast in oblasts:

                    name = str(oblast.get("name", ""))
                    key = str(oblast.get("key", ""))

                    if (
                        "Кіровоград" in name
                        or "кіровоград" in key
                    ):
                        kirovohrad = oblast
                        break

                current_threats = set()

                if kirovohrad:
                    current_threats = detect_threats(kirovohrad)

                # Нова тривога

                if current_threats and not last_threats:

                    await send_to_all(
                        "🚨 ПОВІТРЯНА ТРИВОГА!\n\n"
                        "Кіровоградська область.\n"
                        "Негайно прямуйте в укриття!"
                    )

                # Нові типи загроз

                new_threats = current_threats - last_threats

                if "drone" in new_threats:

                    await send_to_all(
                        "🛩️ БПЛА!\n\n"
                        "Кіровоградська область."
                    )

                if "missile" in new_threats:

                    await send_to_all(
                        "🚀 РАКЕТНА ЗАГРОЗА!\n\n"
                        "Кіровоградська область."
                    )

                if "ballistic" in new_threats:

                    await send_to_all(
                        "💥 БАЛІСТИЧНА ЗАГРОЗА!\n\n"
                        "Кіровоградська область."
                    )

                if "aviation" in new_threats:

                    await send_to_all(
                        "✈️ АВІАЦІЙНА ЗАГРОЗА!\n\n"
                        "Кіровоградська область."
                    )

                if "kab" in new_threats:

                    await send_to_all(
                        "💣 ЗАГРОЗА КАБ!\n\n"
                        "Кіровоградська область."
                    )

                # Відбій

                if last_threats and not current_threats:

                    await send_to_all(
                        "🟢 ВІДБІЙ ПОВІТРЯНОЇ ТРИВОГИ\n\n"
                        "Кіровоградська область."
                    )

                last_threats = current_threats

                logging.info(
                    "Кіровоградська область: %s",
                    current_threats
                )

            except Exception:

                logging.exception(
                    "Помилка перевірки NEPTUN"
                )

            await asyncio.sleep(5)


# --------------------------------------------------
# WEBHOOK
# --------------------------------------------------

async def telegram_webhook(request):

    try:

        data = await request.json()

        await dp.feed_webhook_update(
            bot,
            data
        )

        return web.Response(text="OK")

    except Exception:

        logging.exception(
            "Помилка Telegram webhook"
        )

        return web.Response(
            status=500,
            text="ERROR"
        )


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

async def health(request):

    return web.Response(
        text="Bot is running"
    )


# --------------------------------------------------
# STARTUP
# --------------------------------------------------

async def startup(app):

    logging.info("Запуск бота...")

    await bot.delete_webhook(
        drop_pending_updates=False
    )

    await bot.set_webhook(
        url=WEBHOOK_URL
    )

    logging.info(
        "Webhook встановлено: %s",
        WEBHOOK_URL
    )

    app["alert_task"] = asyncio.create_task(
        check_alerts()
    )


# --------------------------------------------------
# CLEANUP
# --------------------------------------------------

async def cleanup(app):

    app["alert_task"].cancel()

    await bot.delete_webhook()

    await bot.session.close()


# --------------------------------------------------
# SERVER
# --------------------------------------------------

app = web.Application()

app.router.add_get(
    "/",
    health
)

app.router.add_post(
    WEBHOOK_PATH,
    telegram_webhook
)

app.on_startup.append(startup)
app.on_cleanup.append(cleanup)


if __name__ == "__main__":

    web.run_app(
        app,
        host="0.0.0.0",
        port=PORT
    )
