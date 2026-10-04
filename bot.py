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
last_alert_state = False
known_threats = set()


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
async def send_to_all(text):
    for chat_id in list(subscribers):
        try:
            await bot.send_message(chat_id, text)
        except Exception:
            logging.exception("Помилка надсилання")


async def check_alerts():
    global last_alert_state
    global known_threats

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

                kirovohrad_alert = any(
                    "Кіровоград" in str(item)
                    for item in oblasts
                )

                if kirovohrad_alert and not last_alert_state:
                    await send_to_all(
                        "🚨 ПОВІТРЯНА ТРИВОГА!\n\n"
                        "Кіровоградська область.\n"
                        "Негайно прямуйте в укриття!"
                    )

                if not kirovohrad_alert and last_alert_state:
                    await send_to_all(
                        "🟢 ВІДБІЙ ПОВІТРЯНОЇ ТРИВОГИ\n\n"
                        "Кіровоградська область."
                    )

                last_alert_state = kirovohrad_alert

            except Exception:
                logging.exception("Помилка перевірки NEPTUN")

            await asyncio.sleep(5)


async def telegram_polling():
    await bot.delete_webhook(drop_pending_updates=False)
    logging.info("Webhook видалено. Запускаємо Telegram polling.")

    await dp.start_polling(bot)


async def health(request):
    return web.Response(text="Bot is running")


async def startup(app):
    app["telegram_task"] = asyncio.create_task(telegram_polling())
    app["alert_task"] = asyncio.create_task(check_alerts())


async def cleanup(app):
    app["telegram_task"].cancel()
    app["alert_task"].cancel()

    await bot.session.close()


app = web.Application()
app.router.add_get("/", health)

app.on_startup.append(startup)
app.on_cleanup.append(cleanup)


if __name__ == "__main__":
    web.run_app(
        app,
        host="0.0.0.0",
        port=PORT
    )
