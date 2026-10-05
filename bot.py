import os
import asyncio
import logging

from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher
from aiogram.types import Message


# НАЛАШТУВАННЯ

BOT_TOKEN = os.environ["BOT_TOKEN"]
BALLISTIC_BOT_TOKEN = os.environ["BALLISTIC_BOT_TOKEN"]
ROCKET_BOT_TOKEN = os.environ["ROCKET_BOT_TOKEN"]

ALERT_CHAT_ID = os.environ.get("ALERT_CHAT_ID")

PORT = int(os.environ.get("PORT", "10000"))

BASE_URL = "https://telegram-alert-bot-1-yo3t.onrender.com"

DRONE_WEBHOOK_URL = BASE_URL + "/telegram-webhook"
BALLISTIC_WEBHOOK_URL = BASE_URL + "/ballistic-webhook"
ROCKET_WEBHOOK_URL = BASE_URL + "/rocket-webhook"

NEPTUN_URL = "https://neptun.in.ua/api/v1/alerts"

logging.basicConfig(level=logging.INFO)


# БОТИ

drone_bot = Bot(BOT_TOKEN)
ballistic_bot = Bot(BALLISTIC_BOT_TOKEN)
rocket_bot = Bot(ROCKET_BOT_TOKEN)

drone_dp = Dispatcher()
ballistic_dp = Dispatcher()
rocket_dp = Dispatcher()

drone_subscribers = set()
ballistic_subscribers = set()
rocket_subscribers = set()

drone_active = False
ballistic_active = False
rocket_active = False


# ВІДНОВЛЕННЯ ПІДПИСНИКА

def restore_subscribers():

    if not ALERT_CHAT_ID:
        logging.info("ALERT_CHAT_ID ще не заданий")
        return

    try:
        chat_id = int(ALERT_CHAT_ID)

        drone_subscribers.add(chat_id)
        ballistic_subscribers.add(chat_id)
        rocket_subscribers.add(chat_id)

        logging.info(
            "Підписник відновлений: chat_id=%s",
            chat_id
        )

    except ValueError:
        logging.error(
            "ALERT_CHAT_ID має бути числом"
        )


# БОТ БПЛА

@drone_dp.message()
async def handle_drone_message(message: Message):

    if not message.text:
        return

    if message.text.startswith("/start"):

        drone_subscribers.add(message.chat.id)

        logging.info(
            "БПЛА /start від chat_id=%s",
            message.chat.id
        )

        await message.answer(
            "✅ Бот працює!\n\n"
            "Підписка на БПЛА:\n"
            "📍 Кропивницький\n"
            "📍 Кропивницький район\n\n"
            "🛩️ Тільки БПЛА.\n"
            "🔕 Відбій не надсилається."
        )

    elif message.text.startswith("/test"):

        drone_subscribers.add(message.chat.id)

        await message.answer(
            "🧪 ТЕСТ БПЛА\n\n"
            "🛩️ БПЛА!\n\n"
            "Кропивницький / Кропивницький район."
        )


# БОТ БАЛІСТИКИ

@ballistic_dp.message()
async def handle_ballistic_message(message: Message):

    if not message.text:
        return

    if message.text.startswith("/start"):

        ballistic_subscribers.add(message.chat.id)

        logging.info(
            "БАЛІСТИКА /start від chat_id=%s",
            message.chat.id
        )

        await message.answer(
            "✅ Бот працює!\n\n"
            "Підписка на балістику:\n"
            "📍 Кропивницький\n"
            "📍 Кропивницький район\n\n"
            "💥 Тільки балістика.\n"
            "🔕 Відбій не надсилається."
        )

    elif message.text.startswith("/test"):

        ballistic_subscribers.add(message.chat.id)

        await message.answer(
            "🧪 ТЕСТ БАЛІСТИКИ\n\n"
            "💥 БАЛІСТИЧНА ЗАГРОЗА!\n\n"
            "Кропивницький / Кропивницький район."
        )


# БОТ РАКЕТ

@rocket_dp.message()
async def handle_rocket_message(message: Message):

    if not message.text:
        return

    if message.text.startswith("/start"):

        rocket_subscribers.add(message.chat.id)

        logging.info(
            "РАКЕТИ /start від chat_id=%s",
            message.chat.id
        )

        await message.answer(
            "✅ Бот працює!\n\n"
            "Підписка на ракетну небезпеку:\n"
            "📍 Кропивницький\n"
            "📍 Кропивницький район\n\n"
            "🚀 Тільки ракетна загроза.\n"
            "🔕 Відбій не надсилається."
        )

    elif message.text.startswith("/test"):

        rocket_subscribers.add(message.chat.id)

        await message.answer(
            "🧪 ТЕСТ РАКЕТНОЇ НЕБЕЗПЕКИ\n\n"
            "🚀 РАКЕТНА НЕБЕЗПЕКА!\n\n"
            "Кропивницький / Кропивницький район."
        )


# НАДСИЛАННЯ БПЛА

async def send_drone(text):

    for chat_id in list(drone_subscribers):

        try:
            await drone_bot.send_message(
                chat_id,
                text
            )

        except Exception:
            logging.exception(
                "Помилка надсилання БПЛА"
            )


# НАДСИЛАННЯ БАЛІСТИКИ

async def send_ballistic(text):

    for chat_id in list(ballistic_subscribers):

        try:
            await ballistic_bot.send_message(
                chat_id,
                text
            )

        except Exception:
            logging.exception(
                "Помилка надсилання балістики"
            )


# НАДСИЛАННЯ РАКЕТ

async def send_rocket(text):

    for chat_id in list(rocket_subscribers):

        try:
            await rocket_bot.send_message(
                chat_id,
                text
            )

        except Exception:
            logging.exception(
                "Помилка надсилання ракетної небезпеки"
            )


# ВИЗНАЧЕННЯ ТЕРИТОРІЇ

def is_target(item):

    name = str(item.get("name", "")).lower()
    key = str(item.get("key", "")).lower()
    oblast = str(item.get("oblast", "")).lower()

    text = name + " " + key + " " + oblast

    if "кропивницький район" in text:
        return True

    if "кропивницький" in text and "район" not in text:
        return True

    return False


# ВИЗНАЧЕННЯ БПЛА

def is_drone_threat(item):

    reasons = item.get("reasons", [])

    for reason in reasons:

        text = str(reason).lower()

        if (
            "дрон" in text
            or "бпла" in text
            or "безпілот" in text
        ):
            return True

    return False


# ВИЗНАЧЕННЯ БАЛІСТИКИ

def is_ballistic_threat(item):

    reasons = item.get("reasons", [])

    for reason in reasons:

        text = str(reason).lower()

        if "баліст" in text:
            return True

    return False


# ВИЗНАЧЕННЯ РАКЕТ

def is_rocket_threat(item):

    reasons = item.get("reasons", [])

    for reason in reasons:

        text = str(reason).lower()

        if "ракетна загроза" in text:
            return True

    return False


# ПЕРЕВІРКА NEPTUN

async def check_alerts():

    global drone_active
    global ballistic_active
    global rocket_active

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
                current_rocket = False

                for item in alerts.get("raions", []):

                    if not is_target(item):
                        continue

                    if is_drone_threat(item):
                        current_drone = True

                    if is_ballistic_threat(item):
                        current_ballistic = True

                    if is_rocket_threat(item):
                        current_rocket = True

                for item in alerts.get("oblasts", []):

                    if not is_target(item):
                        continue

                    if is_drone_threat(item):
                        current_drone = True

                    if is_ballistic_threat(item):
                        current_ballistic = True

                    if is_rocket_threat(item):
                        current_rocket = True

                if current_drone and not drone_active:

                    await send_drone(
                        "🛩️ БПЛА!\n\n"
                        "Кропивницький / "
                        "Кропивницький район.\n\n"
                        "Стежте за офіційними повідомленнями."
                    )

                if current_ballistic and not ballistic_active:

                    await send_ballistic(
                        "💥 БАЛІСТИЧНА ЗАГРОЗА!\n\n"
                        "Кропивницький / "
                        "Кропивницький район.\n\n"
                        "НЕГАЙНО В УКРИТТЯ!"
                    )

                if current_rocket and not rocket_active:

                    await send_rocket(
                        "🚀 РАКЕТНА НЕБЕЗПЕКА!\n\n"
                        "Кропивницький / "
                        "Кропивницький район.\n\n"
                        "НЕГАЙНО В УКРИТТЯ!"
                    )

                drone_active = current_drone
                ballistic_active = current_ballistic
                rocket_active = current_rocket

                logging.info(
                    "Кропивницький / район — "
                    "БПЛА: %s | Балістика: %s | Ракети: %s",
                    current_drone,
                    current_ballistic,
                    current_rocket
                )

            except Exception:

                logging.exception(
                    "Помилка перевірки NEPTUN"
                )

            await asyncio.sleep(5)


# WEBHOOK БПЛА

async def drone_webhook(request):

    try:

        data = await request.json()

        await drone_dp.feed_webhook_update(
            drone_bot,
            data
        )

        return web.Response(text="OK")

    except Exception:

        logging.exception(
            "Помилка webhook БПЛА"
        )

        return web.Response(
            status=500,
            text="ERROR"
        )


# WEBHOOK БАЛІСТИКИ

async def ballistic_webhook(request):

    try:

        data = await request.json()

        await ballistic_dp.feed_webhook_update(
            ballistic_bot,
            data
        )

        return web.Response(text="OK")

    except Exception:

        logging.exception(
            "Помилка webhook балістики"
        )

        return web.Response(
            status=500,
            text="ERROR"
        )


# WEBHOOK РАКЕТ

async def rocket_webhook(request):

    try:

        data = await request.json()

        await rocket_dp.feed_webhook_update(
            rocket_bot,
            data
        )

        return web.Response(text="OK")

    except Exception:

        logging.exception(
            "Помилка webhook ракет"
        )

        return web.Response(
            status=500,
            text="ERROR"
        )


# HEALTH

async def health(request):

    return web.Response(
        text="Three alert bots are running"
    )


# STARTUP

async def startup(app):

    logging.info(
        "Запуск трьох ботів..."
    )

    restore_subscribers()

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

    await rocket_bot.set_webhook(
        url=ROCKET_WEBHOOK_URL,
        allowed_updates=["message"]
    )

    logging.info(
        "Webhook ракет: %s",
        ROCKET_WEBHOOK_URL
    )

    app["alert_task"] = asyncio.create_task(
        check_alerts()
    )


# CLEANUP

async def cleanup(app):

    task = app.get("alert_task")

    if task:
        task.cancel()

    await drone_bot.session.close()
    await ballistic_bot.session.close()
    await rocket_bot.session.close()


# SERVER

app = web.Application()

app.router.add_get(
    "/",
    health
)

app.router.add_post(
    "/telegram-webhook",
    drone_webhook
)

app.router.add_post(
    "/ballistic-webhook",
    ballistic_webhook
)

app.router.add_post(
    "/rocket-webhook",
    rocket_webhook
)

app.on_startup.append(startup)
app.on_cleanup.append(cleanup)


# ЗАПУСК

if __name__ == "__main__":

    web.run_app(
        app,
        host="0.0.0.0",
        port=PORT
  )
