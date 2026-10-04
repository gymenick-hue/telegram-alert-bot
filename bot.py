import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Message

TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
PORT = int(os.environ.get("PORT", "10000"))

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()


@dp.message()
async def handle_message(message: Message):
    if message.text and message.text.startswith("/start"):
        await message.answer(
            "✅ Бот працює!\n\n"
            "Готовий до підключення сповіщень про різні типи загроз."
        )


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


async def cleanup(app):
    await bot.delete_webhook()
    await bot.session.close()


app = web.Application()

app.router.add_get("/", health)
app.router.add_post("/webhook", webhook)

app.on_startup.append(startup)
app.on_cleanup.append(cleanup)


if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=PORT)
