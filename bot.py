import os
import asyncio
import logging

from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher
from aiogram.types import Message

TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
PORT = int(os.environ.get("PORT", "10000"))

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()

# Користувачі, які натиснули /start
subscribers = set()

# Що вже було відправлено, щоб не дублювати повідомлення
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
            "🟢 Відбій\n\n"
            "Джерело даних: NEPTUN"
        )


async def send_to_all(text):
    for chat_id in list(subscribers):
        try:
            await bot.send_message(chat_id, text)
        except Exception:
            logging.exception("Помилка надсилання повідомлення")


async def check_alerts():
    global last_alert_state
    global known_threats

    await asyncio.sleep(5)

    async with ClientSession() as session:
        while True:
            try:
                # Офіційні тривоги
                async with session.get(
                    "https://neptun.in.ua/api/v1/alerts",
                    timeout=10
                ) as response:
                    alerts = await response.json()

                oblasts = alerts.get("oblasts", [])

                kirovohrad_alert = any(
                    "Кіровоград" in str(item.get("name", ""))
                    or "Кіровоград" in str(item.get("oblast", ""))
                    for item in oblasts
                )

                # Початок тривоги
                if kirovohrad_alert and not last_alert_state:
                    await send_to_all(
                        "🚨 ПОВІТРЯНА ТРИВОГА!\n\n"
                        "Кіровоградська область.\n"
                        "Негайно прямуйте в укриття!\n\n"
                        "Дані: NEPTUN"
                    )

                # Відбій
                if not kirovohrad_alert and last_alert_state:
                    await send_to_all(
                        "🟢 ВІДБІЙ ПОВІТРЯНОЇ ТРИВОГИ\n\n"
                        "Кіровоградська область.\n\n"
                        "Дані: NEPTUN"
                    )

                last_alert_state = kirovohrad_alert

                # Активні загрози
                async with session.get(
                    "https://neptun.in.ua/api/v1/threats",
                    timeout=10
                ) as response:
                    data = await response.json()

                threats = data.get("threats", [])

                current_ids = set()

                for threat in threats:
                    region = str(threat.get("region", ""))

                    if "Кіровоград" not in region:
                        continue

                    if threat.get("status") not in (None, "active"):
                        continue

                    threat_id = threat.get("id")
                    if not threat_id:
                        continue

                    current_ids.add(threat_id)

                    # Уже повідомляли про цю загрозу
                    if threat_id in known_threats:
                        continue

                    threat_type = threat.get("type")
                    title = threat.get("title", "")

                    messages = {
                        "uav": f"🛩️ ЗАГРОЗА БПЛА\n\n{title}\nКіровоградська область.\n\nДані: NEPTUN",
                        "missile": "🚀 РАКЕТНА ЗАГРОЗА\n\nКіровоградська область.\n\nДані: NEPTUN",
                        "ballistic": "💥 БАЛІСТИЧНА ЗАГРОЗА\n\nКіровоградська область.\n\nДані: NEPTUN",
                        "mig31k": "✈️ АВІАЦІЙНА ЗАГРОЗА\n\nМіГ-31К.\n\nДані: NEPTUN",
                        "kab": "💣 ЗАГРОЗА КАБ\n\nКіровоградська область.\n\nДані: NEPTUN",
                        "recon": "🛩️ РОЗВІДУВАЛЬНИЙ БПЛА\n\nКіровоградська область.\n\nДані: NEPTUN",
                    }

                    text = messages.get(threat_type)

                    if text:
                        await send_to_all(text)

                known_threats = current_ids

            except Exception:
                logging.exception("Помилка перевірки NEPTUN")

            # Не частіше одного запиту на 5 секунд
            await asyncio.sleep(5)


async def health(request):
    return web.Response(text="Bot is running")


async def webhook(request):
    try:
        update = await request.json()
        await dp.feed_raw_update(bot, update)
        return web.Response(text="OK")
    except Exception:
        logging.exception("Webhook error")
        return web.Response(text="ERROR", status=500)


async def startup(app):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("Webhook встановлено: %s", WEBHOOK_URL)

    app["alert_task"] = asyncio.create_task(check_alerts())


async def cleanup(app):
    app["alert_task"].cancel()

    try:
        await app["alert_task"]
    except asyncio.CancelledError:
        pass

    await bot.delete_webhook()
    await bot.session.close()


app = web.Application()

app.router.add_get("/", health)
app.router.add_post("/webhook", webhook)

app.on_startup.append(startup)
app.on_cleanup.append(cleanup)


if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=PORT)
