import asyncio
import logging

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from config import config
from services.llm import translate_and_generate
from services.vocabulary import append_to_vocabulary_sheet

logger = logging.getLogger(__name__)

_bot: Bot | None = None
_user_data: dict[int, dict] = {}


def get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(token=config.telegram_bot_token)
    return _bot


async def set_webhook():
    bot = get_bot()
    await bot.set_webhook(url=config.telegram_webhook_url)
    logger.info("Telegram webhook set to %s", config.telegram_webhook_url)


def _build_preview_text(word: str, data: dict) -> str:
    corrected = data.get("corrected_german", word)
    german_label = (
        f"🇩🇪 {corrected}" if corrected == word else f"🇩🇪 {corrected} (← {word})"
    )
    lines = [
        german_label,
        f"🇬🇧 {data['english']}",
        f"🇸🇦 {data['arabic']}",
        "",
        "📝 Example sentences:",
        f"🇩🇪 {data['example_german']}",
        f"🇬🇧 {data['example_english']}",
        f"🇸🇦 {data['example_arabic']}",
    ]
    return "\n".join(lines)


def _build_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("✓ Confirm", callback_data="confirm"),
            InlineKeyboardButton("🔄 Retry", callback_data="retry"),
            InlineKeyboardButton("✕ Cancel", callback_data="cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def handle_start(chat_id: int):
    bot = get_bot()
    await bot.send_message(
        chat_id=chat_id,
        text=(
            "👋 *Willkommen!*\n\n"
            "Send me any German word and I'll:\n"
            "1. Translate it to English and Arabic\n"
            "2. Generate example sentences\n"
            "3. Add it to your Google Sheet vocabulary list"
        ),
    )


async def handle_word(chat_id: int, word: str):
    bot = get_bot()
    try:
        msg = await bot.send_message(
            chat_id=chat_id, text="⏳ Translating and generating examples..."
        )
        data = await asyncio.to_thread(translate_and_generate, word)
        corrected_word = data.get("corrected_german", word)
        _user_data[chat_id] = {
            "word": word,
            "corrected_word": corrected_word,
            "data": data,
        }

        text = _build_preview_text(word, data)
        keyboard = _build_keyboard()
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg.message_id,
            text=text,
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.exception("Failed to process word: %s", word)
        await bot.send_message(
            chat_id=chat_id,
            text=f"❌ Sorry, something went wrong: {e}\n\nPlease try again.",
        )


async def handle_callback(chat_id: int, message_id: int, callback_data: str):
    bot = get_bot()
    user_state = _user_data.get(chat_id)

    if callback_data == "confirm":
        if not user_state:
            await bot.send_message(
                chat_id=chat_id, text="❌ No pending word found. Send a new word!"
            )
            return

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"Adding to your vocabulary sheet...",
            )
            await asyncio.to_thread(
                append_to_vocabulary_sheet,
                word=user_state.get("corrected_word", user_state["word"]),
                english=user_state["data"]["english"],
                arabic=user_state["data"]["arabic"],
                example_german=user_state["data"]["example_german"],
                example_english=user_state["data"]["example_english"],
                example_arabic=user_state["data"]["example_arabic"],
            )
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"✅ Saved!\n\nAdded *{user_state.get('corrected_word', user_state['word'])}* to your vocabulary sheet.",
            )
            _user_data.pop(chat_id, None)
        except Exception as e:
            logger.exception("Failed to append to sheet")
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ Failed to save to Google Sheet: {e}\n\nTry again or send a new word.",
            )

    elif callback_data == "retry":
        if not user_state:
            await bot.send_message(
                chat_id=chat_id, text="❌ No pending word found. Send a new word!"
            )
            return

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="⏳ Retrying translation and generation...",
            )

            data = await asyncio.to_thread(translate_and_generate, user_state["word"])
            user_state["data"] = data
            user_state["corrected_word"] = data.get(
                "corrected_german", user_state["word"]
            )

            text = _build_preview_text(user_state["word"], data)
            keyboard = _build_keyboard()
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.exception("Retry failed")
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ Retry failed: {e}",
            )

    elif callback_data == "cancel":
        _user_data.pop(chat_id, None)
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="✕ Cancelled. Send a new word whenever you want!",
        )
