from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    CommandHandler,
    filters,
)

from config import ADMIN_ID
from handlers.admin_callback import admin_back_keyboard
from database.users import get_all_user_ids


MESSAGE, CONFIRM = range(2)


async def broadcast_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "📢 *Broadcast*\n\n"
        "Jo message sabhi users ko bhejna hai, woh yahan send karo.\n\n"
        "Text, photo, video ya document bhi bhej sakte ho.",
        parse_mode="Markdown",
    )

    return MESSAGE


async def receive_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    context.user_data["broadcast_message"] = update.message

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Send to All",
                callback_data="broadcast_confirm",
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="broadcast_cancel",
            ),
        ]
    ]

    await update.message.reply_text(
        "⚠️ *Broadcast Preview*\n\n"
        "Ye message sabhi registered users ko bheja jayega.\n\n"
        "Kya send karna hai?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return CONFIRM


async def confirm_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text(
            "❌ You are not authorized."
        )
        return ConversationHandler.END

    if query.data == "broadcast_cancel":
        context.user_data.pop("broadcast_message", None)

        await query.edit_message_text(
            "❌ Broadcast cancelled."
        )
        return ConversationHandler.END

    message = context.user_data.get("broadcast_message")

    if not message:
        await query.edit_message_text(
            "❌ Broadcast session expired."
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "📢 Broadcast started...\n\n"
        "Please wait."
    )

    success = 0
    failed = 0

    for user in get_all_user_ids():
        user_id = user["user_id"]

        try:
            await message.copy(
                chat_id=user_id,
            )
            success += 1
        except Exception:
            failed += 1

    await query.message.reply_text(
        "📢 *Broadcast Completed*\n\n"
        f"✅ Sent: {success}\n"
        f"❌ Failed: {failed}",
        reply_markup=admin_back_keyboard(),
        parse_mode="Markdown",
    )

    context.user_data.pop("broadcast_message", None)

    return ConversationHandler.END


async def cancel_broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.pop("broadcast_message", None)

    await update.message.reply_text(
        "❌ Broadcast cancelled."
    )

    return ConversationHandler.END


broadcast_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            broadcast_start,
            pattern=r"^admin_broadcast$",
        )
    ],
    states={
        MESSAGE: [
            MessageHandler(
                filters.ALL & ~filters.COMMAND,
                receive_broadcast,
            )
        ],
        CONFIRM: [
            CallbackQueryHandler(
                confirm_broadcast,
                pattern=r"^broadcast_(confirm|cancel)$",
            )
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_broadcast)
    ],
)
