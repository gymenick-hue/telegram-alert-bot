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

NEPTUN_URL = "https://neptun.in.ua/api/v1/alerts"

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()

subscribers = set()
drone_active = False


@dp.message()
async def handle_message(message: Message):
    if message.text and message.text.startswith("/start"):
        subscribers.add(message.chat.id)

        await message.answer(
            "✅ Бот працює!\n\n"
            "Ви підписані на БПЛА для:\n"
            "📍 м. Кропивницький\n"
            "📍 Кропивницький район\n\n"
            "🛩️ Повідомляю тільки про дронову загрозу.\n"
            "🚫 Ракети, балістика, КАБ та авіація — ігноруються.\n"
            "🔕 Відбій не надсилається."
        )

    elif message.text and message.text.startswith("/test"):
        subscribers.add(message.chat.id)

        await message.answer(
            "🧪 ТЕСТ\n\n"
            "🛩️ БПЛА!\n\n"
            "Кропивницький / Кропивницький район."
        )


async def send_to_all(text):
    for chat_id in list(subscribers):
        try:
            await bot.send_message(chat_id, text)
        except Exception:
            logging.exception("Помилка надсилання")


def is_drone_threat(item):
    """
    Перевіряємо тільки дронову загрозу.
    """
    reasons = item.get("reasons", [])

    for reason in reasons:
        text = str(reason).lower()

        if "дрон" in text or "бпла" in text:
            return True

    return False


def is_target(item):
    """
    Перевіряємо Кропивницький район та Кропивницький.
    """
    name = str(item.get("name", "")).lower()
    key = str(item.get("key", "")).lower()
    oblast = str(item.get("oblast", "")).lower()

    text = f"{name} {key} {oblast}"

    if "кропивницький район" in text:
        return True

    if "кропивницький" in text and "район" not in text:
        return True

    return False


async def check_alerts():
    global drone_active

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

                # Перевіряємо райони
                for item in alerts.get("raions", []):
                    if is_target(item) and is_drone_threat(item):
                        current_drone = True
                        break

                # Також перевіряємо області на випадок,
                # якщо NEPTUN передасть Кропивницький окремим записом
                if not current_drone:
                    for item in alerts.get("oblasts", []):
                        if is_target(item) and is_drone_threat(item):
                            current_drone = True
                            break

                # Повідомляємо тільки в момент появи загрози
                if current_drone and not drone_active:
                    await send_to_all(
                        "🛩️ БПЛА!\n\n"
                        "Кропивницький / Кропивницький район.\n"
                        "Будьте уважні та стежте за офіційними повідомленнями."
                    )

                # Відбій НЕ надсилаємо
                drone_active = current_drone

                logging.info(
                    "Кропивницький / район — БПЛА: %s",
                    current_drone
                )

            except Exception:
                logging.exception("Помилка перевірки NEPTUN")

            await asyncio.sleep(5)


async def telegram_webhook(request):
    try:
        data = await request.json()

        await dp.feed_webhook_update(bot, data)

        return web.Response(text="OK")

    except Exception:
        logging.exception("Помилка Telegram webhook")
        return web.Response(
            status=500,
            text="ERROR"
        )


async def health(request):
    return web.Response(text="Bot is running")


async def startup(app):
    logging.info("Запуск бота...")

    await bot.set_webhook(
        url=WEBHOOK_URL,
        allowed_updates=["message"]
    )

    logging.info(
        "Webhook встановлено: %s",
        WEBHOOK_URL
    )

    app["alert_task"] = asyncio.create_task(
        check_alerts()
    )


async def cleanup(app):
    app["alert_task"].cancel()
    await bot.session.close()


app = web.Application()

app.router.add_get("/", health)
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
