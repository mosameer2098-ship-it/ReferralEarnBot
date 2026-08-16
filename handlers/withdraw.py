from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import MIN_WITHDRAW
from database.users import get_user, deduct_balance
from database.withdrawals import create_withdrawal


AMOUNT, UPI_ID, CONFIRM = range(3)


def withdraw_cancel_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="withdraw_cancel",
                )
            ]
        ]
    )


def withdraw_confirm_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Confirm",
                    callback_data="withdraw_confirm",
                ),
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="withdraw_cancel",
                ),
            ]
        ]
    )


async def start_withdraw(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user = get_user(query.from_user.id)

    if not user:
        await query.edit_message_text(
            "❌ Account not found.\n\n"
            "Please use /start first."
        )
        return ConversationHandler.END

    balance = float(user.get("balance", 0))

    if balance < MIN_WITHDRAW:
        await query.edit_message_text(
            "💸 *Withdraw*\n\n"
            f"💰 Your Balance: ₹{balance:g}\n"
            f"📌 Minimum Withdrawal: ₹{MIN_WITHDRAW:g}\n\n"
            f"❌ You need at least ₹{MIN_WITHDRAW:g} to withdraw.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Back to Dashboard",
                            callback_data="back_dashboard",
                        )
                    ]
                ]
            ),
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "💸 *Withdrawal Request*\n\n"
        f"💰 Available Balance: ₹{balance:g}\n"
        f"📌 Minimum: ₹{MIN_WITHDRAW:g}\n\n"
        "✏️ Enter the amount you want to withdraw:",
        reply_markup=withdraw_cancel_keyboard(),
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
            "Please enter a valid number.",
            reply_markup=withdraw_cancel_keyboard(),
        )
        return AMOUNT

    if amount <= 0:
        await update.message.reply_text(
            "❌ Amount must be greater than ₹0.",
            reply_markup=withdraw_cancel_keyboard(),
        )
        return AMOUNT

    user = get_user(update.effective_user.id)

    if not user:
        await update.message.reply_text(
            "❌ Account not found."
        )
        return ConversationHandler.END

    balance = float(user.get("balance", 0))

    if amount < MIN_WITHDRAW:
        await update.message.reply_text(
            f"❌ Minimum withdrawal is ₹{MIN_WITHDRAW:g}.",
            reply_markup=withdraw_cancel_keyboard(),
        )
        return AMOUNT

    if amount > balance:
        await update.message.reply_text(
            "❌ Insufficient balance.\n\n"
            f"💰 Your balance: ₹{balance:g}",
            reply_markup=withdraw_cancel_keyboard(),
        )
        return AMOUNT

    context.user_data["withdraw_amount"] = amount

    await update.message.reply_text(
        "💳 *Enter your UPI ID*\n\n"
        "Example: `name@upi`",
        reply_markup=withdraw_cancel_keyboard(),
        parse_mode="Markdown",
    )

    return UPI_ID


async def receive_upi(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    upi_id = update.message.text.strip()
    amount = context.user_data.get("withdraw_amount")

    if not amount:
        return ConversationHandler.END

    if not upi_id or "@" not in upi_id or " " in upi_id:
        await update.message.reply_text(
            "❌ Invalid UPI ID.\n\n"
            "Example: `name@upi`\n\n"
            "Please enter a valid UPI ID.",
            reply_markup=withdraw_cancel_keyboard(),
            parse_mode="Markdown",
        )
        return UPI_ID

    context.user_data["withdraw_upi"] = upi_id

    await update.message.reply_text(
        "📋 *Confirm Withdrawal*\n\n"
        f"💰 Amount: ₹{float(amount):g}\n"
        f"💳 UPI ID: `{upi_id}`\n\n"
        "⚠️ Please check the details carefully.\n"
        "The amount will be deducted only after confirmation.",
        reply_markup=withdraw_confirm_keyboard(),
        parse_mode="Markdown",
    )

    return CONFIRM


async def confirm_withdraw(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    amount = context.user_data.get("withdraw_amount")
    upi_id = context.user_data.get("withdraw_upi")

    if not amount or not upi_id:
        context.user_data.clear()

        await query.edit_message_text(
            "❌ Withdrawal session expired.\n\n"
            "Please start again."
        )
        return ConversationHandler.END

    # Deduct only after confirmation.
    deducted = deduct_balance(
        user_id,
        float(amount),
    )

    if not deducted:
        context.user_data.clear()

        await query.edit_message_text(
            "❌ Withdrawal failed.\n\n"
            "Your balance may have changed. "
            "Please try again."
        )
        return ConversationHandler.END

    withdrawal_id = create_withdrawal(
        user_id=user_id,
        amount=float(amount),
        upi_id=upi_id,
    )

    context.user_data.clear()

    await query.edit_message_text(
        "✅ *Withdrawal Request Submitted!*\n\n"
        f"💰 Amount: ₹{float(amount):g}\n"
        f"💳 UPI: `{upi_id}`\n"
        f"🆔 Request ID: `{withdrawal_id}`\n\n"
        "⏳ Status: Pending\n\n"
        "💡 Your request has been sent to the admin.",
        parse_mode="Markdown",
    )

    return ConversationHandler.END


async def cancel_withdraw(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.clear()

    if update.callback_query:
        query = update.callback_query
        await query.answer()

        from handlers.menu import show_menu

        await show_menu(
            update,
            context,
        )
    else:
        await update.message.reply_text(
            "❌ Withdrawal cancelled."
        )

    return ConversationHandler.END


withdraw_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            start_withdraw,
            pattern="^withdraw$",
        )
    ],
    states={
        AMOUNT: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_amount,
            ),
            CallbackQueryHandler(
                cancel_withdraw,
                pattern="^withdraw_cancel$",
            ),
        ],
        UPI_ID: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_upi,
            ),
            CallbackQueryHandler(
                cancel_withdraw,
                pattern="^withdraw_cancel$",
            ),
        ],
        CONFIRM: [
            CallbackQueryHandler(
                confirm_withdraw,
                pattern="^withdraw_confirm$",
            ),
            CallbackQueryHandler(
                cancel_withdraw,
                pattern="^withdraw_cancel$",
            ),
        ],
    },
    fallbacks=[
        CommandHandler(
            "cancel",
            cancel_withdraw,
        ),
    ],
)
