import asyncio
import logging

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse
from telegram.error import BadRequest

from config import config
from services.telegram_bot import get_bot, handle_start, handle_word, handle_callback

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_handler(handler_name: str, coro):
    try:
        await coro
    except Exception:
        logger.exception("%s failed", handler_name)


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    secret_token = config.telegram_webhook_secret_token
    received = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if received != secret_token:
        logger.warning("Rejected webhook with invalid secret token")
        return JSONResponse({"ok": False}, status_code=403)

    try:
        data = await request.json()
    except Exception as e:
        logger.error("Invalid JSON in webhook: %s", e)
        return JSONResponse({"ok": False}, status_code=200)

    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if text.startswith("/start"):
            asyncio.create_task(_run_handler("handle_start", handle_start(chat_id)))
        elif text.strip():
            asyncio.create_task(
                _run_handler("handle_word", handle_word(chat_id, text.strip()))
            )

    elif "callback_query" in data:
        callback = data["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        message_id = callback["message"]["message_id"]
        callback_data = callback.get("data", "")

        bot = get_bot()
        try:
            await bot.answer_callback_query(callback["id"])
        except BadRequest as e:
            logger.warning("Stale callback query %s: %s", callback["id"], e)

        asyncio.create_task(
            _run_handler(
                "handle_callback",
                handle_callback(chat_id, message_id, callback_data),
            )
        )

    return JSONResponse({"ok": True})
