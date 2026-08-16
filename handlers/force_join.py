from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from config import FORCE_CHANNELS


def is_member(member):
    return member.status in ("member", "administrator", "creator")


async def check_force_join(
    user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
):
    missing = []

    for channel in FORCE_CHANNELS:
        try:
            member = await context.bot.get_chat_member(
                chat_id=channel["username"],
                user_id=user_id,
            )

            if not is_member(member):
                missing.append(channel)

        except Exception:
            missing.append(channel)

    return missing


def force_join_keyboard(missing):
    buttons = []

    for channel in missing:
        username = channel["username"].lstrip("@")

        buttons.append(
            [
                InlineKeyboardButton(
                    f"{channel['name']}",
                    url=f"https://t.me/{username}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                "✅ Check Membership",
                callback_data="check_force_join",
            )
        ]
    )

    return InlineKeyboardMarkup(buttons)


async def show_force_join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    missing,
):
    text = (
        "🔒 *Join Required*\n\n"
        "Bot use karne ke liye pehle hamare "
        "teeno channels join karein.\n\n"
        "Join karne ke baad neeche "
        "✅ Check Membership button dabayein."
    )

    keyboard = force_join_keyboard(missing)

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown",
            )
        except Exception as error:
            if "Message is not modified" in str(error):
                await update.callback_query.answer(
                    "❌ Abhi bhi channel join nahi hai.",
                    show_alert=True,
                )
            else:
                raise

    elif update.message:
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
