import logging

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from services.telegram_bot import get_bot, handle_start, handle_word, handle_callback

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
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
            await handle_start(chat_id)
        elif text.strip():
            await handle_word(chat_id, text.strip())

    elif "callback_query" in data:
        callback = data["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        message_id = callback["message"]["message_id"]
        callback_data = callback.get("data", "")

        bot = get_bot()
        await bot.answer_callback_query(callback["id"])
        await handle_callback(chat_id, message_id, callback_data)

    return JSONResponse({"ok": True})
