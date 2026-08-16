from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from config import ADMIN_ID
from database.mongodb import (
    users_collection,
    withdrawals_collection,
)


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


def admin_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📋 Pending Withdrawals",
                    callback_data="admin_withdrawals",
                )
            ],
            [
                InlineKeyboardButton(
                    "📜 Withdrawal History",
                    callback_data="admin_history",
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ Add Balance",
                    callback_data="admin_add_balance",
                ),
                InlineKeyboardButton(
                    "➖ Deduct Balance",
                    callback_data="admin_deduct_balance",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📢 Broadcast",
                    callback_data="admin_broadcast",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Refresh",
                    callback_data="admin_refresh",
                )
            ],
        ]
    )


def get_admin_text():
    total_users = users_collection.count_documents({})

    pending_withdrawals = (
        withdrawals_collection.count_documents(
            {"status": "pending"}
        )
    )

    total_earned_result = list(
        users_collection.aggregate(
            [
                {
                    "$group": {
                        "_id": None,
                        "total": {
                            "$sum": "$total_earned"
                        },
                    }
                }
            ]
        )
    )

    total_earned = (
        total_earned_result[0]["total"]
        if total_earned_result
        else 0
    )

    return (
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "       👑 *ADMIN PANEL*\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"👥 *Total Users:* {total_users}\n"
        f"💸 *Pending Withdrawals:* "
        f"{pending_withdrawals}\n"
        f"💰 *Total Earned:* ₹{total_earned:g}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🛠 *ADMIN CONTROLS*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 Choose an option below:"
    )


async def admin_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text(
            "❌ You are not authorized "
            "to use the admin panel."
        )
        return

    await update.message.reply_text(
        get_admin_text(),
        reply_markup=admin_keyboard(),
        parse_mode="Markdown",
    )
