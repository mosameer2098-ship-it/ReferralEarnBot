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
from database.users import get_user_by_id, admin_add_balance
from handlers.admin_callback import admin_back_keyboard


USER_ID, AMOUNT, CONFIRM = range(3)


async def add_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return ConversationHandler.END

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "➕ *Add Balance*\n\n"
        "👤 User ID bhejo:\n\n"
        "Example:\n"
        "`123456789`",
        parse_mode="Markdown",
    )

    return USER_ID


async def receive_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            "Pehle bot start karne wale user ka valid Telegram ID bhejo."
        )
        return USER_ID

    context.user_data["admin_balance_user_id"] = user_id

    await update.message.reply_text(
        f"👤 User ID: `{user_id}`\n"
        f"💰 Current Balance: ₹{float(user.get('balance', 0)):g}\n\n"
        "Ab amount bhejo:",
        parse_mode="Markdown",
    )

    return AMOUNT


async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount.\n\n"
            "Example: `100`",
            parse_mode="Markdown",
        )
        return AMOUNT

    if amount <= 0:
        await update.message.reply_text(
            "❌ Amount 0 se greater hona chahiye."
        )
        return AMOUNT

    context.user_data["admin_balance_amount"] = amount

    user_id = context.user_data["admin_balance_user_id"]

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Confirm",
                callback_data="admin_add_balance_confirm",
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="admin_add_balance_cancel",
            ),
        ]
    ]

    await update.message.reply_text(
        "⚠️ *Confirm Balance Addition*\n\n"
        f"👤 User ID: `{user_id}`\n"
        f"💰 Amount: ₹{amount:g}\n\n"
        "Kya balance add karna hai?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

    return CONFIRM


async def confirm_add_balance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ You are not authorized.")
        return ConversationHandler.END

    if query.data == "admin_add_balance_cancel":
        context.user_data.pop("admin_balance_user_id", None)
        context.user_data.pop("admin_balance_amount", None)

        await query.edit_message_text(
            "❌ Balance addition cancelled.",
            reply_markup=admin_back_keyboard(),
        )
        return ConversationHandler.END

    user_id = context.user_data.get("admin_balance_user_id")
    amount = context.user_data.get("admin_balance_amount")

    if not user_id or not amount:
        await query.edit_message_text(
            "❌ Session expired. Please try again."
        )
        return ConversationHandler.END

    success = admin_add_balance(user_id, amount)

    if not success:
        await query.edit_message_text(
            "❌ Balance update failed."
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "✅ *Balance Added Successfully*\n\n"
        f"👤 User ID: `{user_id}`\n"
        f"💰 Added: ₹{amount:g}",
        reply_markup=admin_back_keyboard(),
        parse_mode="Markdown",
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "💰 *Balance Added!*\n\n"
                f"Amount Added: ₹{amount:g}\n\n"
                "Your bot balance has been updated."
            ),
            parse_mode="Markdown",
        )
    except Exception:
        pass

    context.user_data.pop("admin_balance_user_id", None)
    context.user_data.pop("admin_balance_amount", None)

    return ConversationHandler.END


async def cancel_add_balance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.pop("admin_balance_user_id", None)
    context.user_data.pop("admin_balance_amount", None)

    await update.message.reply_text(
        "❌ Add Balance cancelled."
    )

    return ConversationHandler.END


async def add_balance_existing_user(
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

    try:
        user_id = int(query.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await query.edit_message_text(
            "❌ Invalid user ID."
        )
        return ConversationHandler.END

    user = get_user_by_id(user_id)

    if not user:
        await query.edit_message_text(
            "❌ User not found.",
            reply_markup=admin_back_keyboard(),
        )
        return ConversationHandler.END

    context.user_data["admin_balance_user_id"] = user_id

    balance = float(user.get("balance", 0))

    await query.edit_message_text(
        "➕ Add Balance\n\n"
        f"👤 User ID: {user_id}\n"
        f"💰 Current Balance: ₹{balance:g}\n\n"
        "💵 Ab kitna amount add karna hai?"
    )

    return AMOUNT


add_balance_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            add_balance_start,
            pattern=r"^admin_add_balance$",
        ),
        CallbackQueryHandler(
            add_balance_existing_user,
            pattern=r"^admin_add_user:[0-9]+$",
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
                confirm_add_balance,
                pattern=r"^admin_add_balance_(confirm|cancel)$",
            )
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_add_balance)
    ],
)
