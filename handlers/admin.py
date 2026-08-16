from datetime import datetime, timedelta, timezone
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
                    "🔎 Find User",
                    callback_data="admin_find_user",
                )
                ],
                [
                    InlineKeyboardButton(
                        "📊 Analytics",
                        callback_data="admin_analytics",
                    )
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


def get_analytics_text():
    total_users = users_collection.count_documents({})

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_start = now - timedelta(days=7)
    thirty_days_start = now - timedelta(days=30)

    today_users = users_collection.count_documents({
        "created_at": {"$gte": today_start}
    })

    seven_days_users = users_collection.count_documents({
        "created_at": {"$gte": seven_days_start}
    })

    thirty_days_users = users_collection.count_documents({
        "created_at": {"$gte": thirty_days_start}
    })

    blocked_users = users_collection.count_documents(
        {"blocked": True}
    )

    active_users = total_users - blocked_users

    referral_result = list(
        users_collection.aggregate([
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$referral_count"}
                }
            }
        ])
    )

    total_referrals = (
        referral_result[0]["total"]
        if referral_result
        else 0
    )

    balance_result = list(
        users_collection.aggregate([
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$balance"}
                }
            }
        ])
    )

    total_balance = (
        balance_result[0]["total"]
        if balance_result
        else 0
    )

    earned_result = list(
        users_collection.aggregate([
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$total_earned"}
                }
            }
        ])
    )

    total_earned = (
        earned_result[0]["total"]
        if earned_result
        else 0
    )

    total_withdrawals = withdrawals_collection.count_documents({})

    pending_withdrawals = withdrawals_collection.count_documents(
        {"status": "pending"}
    )

    approved_withdrawals = withdrawals_collection.count_documents(
        {"status": "approved"}
    )

    rejected_withdrawals = withdrawals_collection.count_documents(
        {"status": "rejected"}
    )

    pending_amount_result = list(
        withdrawals_collection.aggregate([
            {"$match": {"status": "pending"}},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$amount"}
                }
            }
        ])
    )

    pending_amount = (
        pending_amount_result[0]["total"]
        if pending_amount_result
        else 0
    )

    approved_amount_result = list(
        withdrawals_collection.aggregate([
            {"$match": {"status": "approved"}},
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$amount"}
                }
            }
        ])
    )

    approved_amount = (
        approved_amount_result[0]["total"]
        if approved_amount_result
        else 0
    )

    return (
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "       📊 *ANALYTICS*\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

        "👥 *USER STATISTICS*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Total Users: *{total_users}*\n"
        f"🟢 Active Users: *{active_users}*\n"
        f"🚫 Blocked Users: *{blocked_users}*\n"
                f"🆕 New Today: *{today_users}*\n"
                f"📅 New Last 7 Days: *{seven_days_users}*\n"
                f"🗓 New Last 30 Days: *{thirty_days_users}*\n"

        f"👥 Total Referrals: *{total_referrals}*\n\n"

        "💰 *BALANCE STATISTICS*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 User Balance: *₹{total_balance:g}*\n"
        f"💎 Total Earned: *₹{total_earned:g}*\n\n"

        "💸 *WITHDRAWAL STATISTICS*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 Total Requests: *{total_withdrawals}*\n"
        f"⏳ Pending: *{pending_withdrawals}*\n"
        f"✅ Approved: *{approved_withdrawals}*\n"
        f"❌ Rejected: *{rejected_withdrawals}*\n"
        f"⏳ Pending Amount: *₹{pending_amount:g}*\n"
        f"✅ Approved Amount: *₹{approved_amount:g}*"
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
