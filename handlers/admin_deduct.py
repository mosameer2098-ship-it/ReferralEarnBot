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
from database.users import get_user_by_id, admin_deduct_balance
from handlers.admin_callback import admin_back_keyboard


USER_ID, AMOUNT, CONFIRM = range(3)


async def deduct_balance_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "➖ *Deduct Balance*\n\n"
        "👤 User ID bhejo:\n\n"
        "Example:\n"
        "`123456789`",
        parse_mode="Markdown",
    )

    return USER_ID


async def receive_user_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        user_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid User ID.\n\n"
            "Sirf numeric User ID bhejo."
        )
        return USER_ID

    user = get_user_by_id(user_id)

    if not user:
        await update.message.reply_text(
            "❌ User nahi mila.\n\n"
            "Valid Telegram User ID bhejo."
        )
        return USER_ID

    context.user_data["admin_deduct_user_id"] = user_id

    balance = float(user.get("balance", 0))

    await update.message.reply_text(
        f"👤 User ID: `{user_id}`\n"
        f"💰 Current Balance: ₹{balance:g}\n\n"
        "Ab deduct amount bhejo:",
        parse_mode="Markdown",
    )

    return AMOUNT


async def receive_amount(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount.\n\n"
            "Example: `50`",
            parse_mode="Markdown",
        )
        return AMOUNT

    if amount <= 0:
        await update.message.reply_text(
            "❌ Amount 0 se greater hona chahiye."
        )
        return AMOUNT

    user_id = context.user_data["admin_deduct_user_id"]
    user = get_user_by_id(user_id)
    balance = float(user.get("balance", 0))

    if amount > balance:
        await update.message.reply_text(
            f"❌ Insufficient balance.\n\n"
            f"💰 Current Balance: ₹{balance:g}\n"
            f"➖ You tried to deduct: ₹{amount:g}"
        )
        return AMOUNT

    context.user_data["admin_deduct_amount"] = amount

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Confirm",
                callback_data="admin_deduct_confirm",
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="admin_deduct_cancel",
            ),
        ]
    ]

    await update.message.reply_text(
        "⚠️ *Confirm Balance Deduction*\n\n"
        f"👤 User ID: `{user_id}`\n"
        f"💰 Current Balance: ₹{balance:g}\n"
        f"➖ Deduct: ₹{amount:g}\n\n"
        "Continue?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return CONFIRM


async def confirm_deduct_balance(
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

    if query.data == "admin_deduct_cancel":
        context.user_data.pop("admin_deduct_user_id", None)
        context.user_data.pop("admin_deduct_amount", None)

        await query.edit_message_text(
            "❌ Balance deduction cancelled."
        )
        return ConversationHandler.END

    user_id = context.user_data.get("admin_deduct_user_id")
    amount = context.user_data.get("admin_deduct_amount")

    if not user_id or not amount:
        await query.edit_message_text(
            "❌ Session expired. Please try again."
        )
        return ConversationHandler.END

    success = admin_deduct_balance(user_id, amount)

    if not success:
        await query.edit_message_text(
            "❌ Balance deduction failed.\n\n"
            "The user's balance may have changed."
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "✅ *Balance Deducted Successfully*\n\n"
        f"👤 User ID: `{user_id}`\n"
        f"➖ Deducted: ₹{amount:g}",
        reply_markup=admin_back_keyboard(),
        parse_mode="Markdown",
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "⚠️ *Balance Updated*\n\n"
                f"Amount Deducted: ₹{amount:g}\n\n"
                "Your bot balance has been updated."
            ),
            parse_mode="Markdown",
        )
    except Exception:
        pass

    context.user_data.pop("admin_deduct_user_id", None)
    context.user_data.pop("admin_deduct_amount", None)

    return ConversationHandler.END


async def cancel_deduct_balance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.pop("admin_deduct_user_id", None)
    context.user_data.pop("admin_deduct_amount", None)

    await update.message.reply_text(
        "❌ Deduct Balance cancelled."
    )

    return ConversationHandler.END


deduct_balance_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            deduct_balance_start,
            pattern=r"^admin_deduct_balance$",
        )
    ],
    states={
        USER_ID: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_user_id,
            )
        ],
        AMOUNT: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_amount,
            )
        ],
        CONFIRM: [
            CallbackQueryHandler(
                confirm_deduct_balance,
                pattern=r"^admin_deduct_(confirm|cancel)$",
            )
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_deduct_balance)
    ],
)
