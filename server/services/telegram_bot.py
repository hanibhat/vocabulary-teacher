import asyncio
import logging

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from config import config
from services.llm import translate_and_generate
from services.vocabulary import append_to_vocabulary_sheet

logger = logging.getLogger(__name__)

_bot: Bot | None = None
_user_data: dict[tuple[int, int], dict] = {}


def get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(token=config.telegram_bot_token)
    return _bot


async def set_telegram_webhook():
    bot = get_bot()
    await bot.set_webhook(
        url=config.telegram_webhook_url,
        secret_token=config.telegram_webhook_secret_token,
    )
    logger.info("Telegram webhook set to %s", config.telegram_webhook_url)
    admin_chat_id = config.telegram_admin_chat_id
    if admin_chat_id:
        await bot.send_message(
            chat_id=admin_chat_id,
            text=f"✅ Bot connected — webhook set to {config.telegram_webhook_url}",
        )


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
            chat_id=chat_id, text=f'⏳ Translating "{word}"...'
        )
        data = await asyncio.to_thread(translate_and_generate, word)
        corrected_word = data.get("corrected_german", word)
        _user_data[(chat_id, msg.message_id)] = {
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
            text=f'❌ Sorry, something went wrong when processing "{word}": {e}',
        )


async def handle_callback(chat_id: int, message_id: int, callback_data: str):
    bot = get_bot()
    user_state = _user_data.get((chat_id, message_id))

    if callback_data == "cancel":
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="✕ Cancelled.",
        )
        _user_data.pop((chat_id, message_id), None)

    elif callback_data == "confirm":
        if not user_state:
            return

        _user_data.pop((chat_id, message_id), None)
        word = user_state.get("corrected_word", user_state["word"])
        try:
            msg = await bot.send_message(
                chat_id=chat_id,
                text=f'Adding "{word}" to your vocabulary sheet...',
            )
            await asyncio.to_thread(
                append_to_vocabulary_sheet,
                word=word,
                english=user_state["data"]["english"],
                arabic=user_state["data"]["arabic"],
                example_german=user_state["data"]["example_german"],
                example_english=user_state["data"]["example_english"],
                example_arabic=user_state["data"]["example_arabic"],
            )
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg.message_id,
                text=f'✅ Saved!\n\nAdded "{word}" to your vocabulary sheet.',
            )
            _user_data.pop((chat_id, message_id), None)
        except Exception as e:
            logger.exception("Failed to append to sheet")
            await bot.send_message(
                chat_id=chat_id,
                text=f'❌ Failed to save "{word}": {e}',
            )

    elif callback_data == "retry":
        if not user_state:
            return

        word = user_state["word"]
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f'⏳ Retrying translation of "{word}"...',
            )
            data = await asyncio.to_thread(translate_and_generate, word)
            user_state["data"] = data
            user_state["corrected_word"] = data.get("corrected_german", word)
            text = _build_preview_text(word, data)
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
                text=f'❌ Retry failed for "{word}": {e}',
            )
