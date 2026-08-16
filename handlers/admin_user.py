from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

from config import ADMIN_ID
from database.users import (
    get_user_by_id,
    is_user_blocked,
    set_user_blocked,
)
from database.withdrawals import get_user_withdrawals


USER_ID = 1


def admin_user_keyboard(user_id=None):
    buttons = []

    if user_id:
        buttons.append([
            InlineKeyboardButton(
                "➕ Add Balance",
                callback_data=f"admin_add_user:{user_id}",
            ),
            InlineKeyboardButton(
                "➖ Deduct Balance",
                callback_data=f"admin_deduct_user:{user_id}",
            ),
        ])

        buttons.append([
            InlineKeyboardButton(
                "📜 Withdrawal History",
                callback_data=f"admin_user_history:{user_id}",
            )
        ])

        if is_user_blocked(user_id):
            buttons.append([
                InlineKeyboardButton(
                    "✅ Unblock User",
                    callback_data=f"admin_unblock_user:{user_id}",
                )
            ])
        else:
            buttons.append([
                InlineKeyboardButton(
                    "🚫 Block User",
                    callback_data=f"admin_block_user:{user_id}",
                )
            ])

    buttons.append([
        InlineKeyboardButton(
            "🔙 Back to Admin Panel",
            callback_data="admin_back",
        )
    ])

    return InlineKeyboardMarkup(buttons)


async def start_find_user(
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

    await query.edit_message_text(
        "🔎 Find User\n\n"
        "🆔 Please send the Telegram User ID:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="admin_find_cancel",
                )
            ]
        ]),
        
    )

    return USER_ID


async def receive_user_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    try:
        user_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid User ID.\n\n"
            "Please send numbers only."
        )
        return USER_ID

    user = get_user_by_id(user_id)

    if not user:
        await update.message.reply_text(
            "❌ User Not Found\n\n"
            f"🆔 User ID: {user_id}\n\n"
            "This user is not registered in the bot.",
            reply_markup=admin_user_keyboard(user_id),
        )
        return ConversationHandler.END

    username = user.get("username") or "N/A"
    first_name = user.get("first_name") or "N/A"
    balance = float(user.get("balance", 0))
    total_earned = float(user.get("total_earned", 0))
    referrals = int(user.get("referral_count", 0))

    created_at = user.get("created_at")

    if created_at:
        created_text = created_at.strftime(
            "%d %b %Y • %I:%M %p"
        )
    else:
        created_text = "N/A"

    text = (
        "👤 USER DETAILS\n\n"
        f"🆔 User ID: {user_id}\n"
        f"👤 Name: {first_name}\n"
        f"🔹 Username: @{username if username != 'N/A' else 'N/A'}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Balance: ₹{balance:g}\n"
        f"💎 Total Earned: ₹{total_earned:g}\n"
        f"👥 Referrals: {referrals}\n"
        f"📅 Joined: {created_text}"
    )

    await update.message.reply_text(
        text,
        reply_markup=admin_user_keyboard(user_id),
        
    )

    return ConversationHandler.END


async def toggle_user_block(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text(
            "❌ You are not authorized."
        )
        return

    try:
        action, user_id_text = query.data.split(":", 1)
        user_id = int(user_id_text)
    except (ValueError, IndexError):
        await query.edit_message_text(
            "❌ Invalid user ID."
        )
        return

    user = get_user_by_id(user_id)

    if not user:
        await query.edit_message_text(
            "❌ User not found.",
            reply_markup=admin_back_keyboard(),
        )
        return

    if action == "admin_block_user":
        success = set_user_blocked(user_id, True)
        message = (
            "🚫 User Blocked Successfully"
            if success
            else "❌ Failed to block user."
        )
    else:
        success = set_user_blocked(user_id, False)
        message = (
            "✅ User Unblocked Successfully"
            if success
            else "❌ Failed to unblock user."
        )

    await query.edit_message_text(
        message,
        reply_markup=admin_user_keyboard(user_id),
    )


async def show_user_withdrawal_history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text(
            "❌ You are not authorized."
        )
        return

    try:
        user_id = int(query.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await query.edit_message_text(
            "❌ Invalid user ID."
        )
        return

    withdrawals = list(get_user_withdrawals(user_id, limit=20))

    if not withdrawals:
        await query.edit_message_text(
            f"📜 Withdrawal History\n\n"
            f"👤 User ID: {user_id}\n\n"
            "📭 No withdrawal requests found.",
            reply_markup=admin_user_keyboard(user_id),
        )
        return

    lines = [
        "📜 Withdrawal History",
        "",
        f"👤 User ID: {user_id}",
        "",
    ]

    for index, withdrawal in enumerate(withdrawals, 1):
        amount = float(withdrawal.get("amount", 0))
        upi_id = withdrawal.get("upi_id", "N/A")
        status = withdrawal.get("status", "unknown")

        if status == "pending":
            status_text = "⏳ Pending"
        elif status == "approved":
            status_text = "✅ Approved"
        elif status == "rejected":
            status_text = "❌ Rejected"
        else:
            status_text = f"⚠️ {status}"

        created_at = withdrawal.get("created_at")

        if created_at:
            created_text = created_at.strftime(
                "%d %b %Y • %I:%M %p"
            )
        else:
            created_text = "N/A"

        withdrawal_id = str(
            withdrawal.get("_id", "N/A")
        )

        lines.extend([
            f"#{index} • {status_text}",
            f"💰 Amount: ₹{amount:g}",
            f"💳 UPI: {upi_id}",
            f"📅 Date: {created_text}",
            f"🆔 ID: {withdrawal_id}",
            "",
        ])

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=admin_user_keyboard(user_id),
    )


async def cancel_find_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        from handlers.admin import get_admin_text, admin_keyboard

        await query.edit_message_text(
            get_admin_text(),
            reply_markup=admin_keyboard(),
        )

    return ConversationHandler.END


find_user_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            start_find_user,
            pattern="^admin_find_user$",
        )
    ],
    states={
        USER_ID: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_user_id,
            ),
            CallbackQueryHandler(
                cancel_find_user,
                pattern="^admin_find_cancel$",
            ),
        ],
    },
    fallbacks=[
        CommandHandler(
            "cancel",
            cancel_find_user,
        )
    ],
)
