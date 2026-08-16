from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from database.users import get_user
from handlers.force_join import (
    check_force_join,
    show_force_join,
)


def main_menu():
    keyboard = [
        [
            InlineKeyboardButton("💰 Balance", callback_data="balance"),
            InlineKeyboardButton("👥 Referrals", callback_data="referrals"),
        ],
        [
            InlineKeyboardButton("🔗 Referral Link", callback_data="referral_link"),
            InlineKeyboardButton("📊 My Stats", callback_data="stats"),
        ],
        [
            InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
        ],
        [
            InlineKeyboardButton(
                "📜 Withdrawal History",
                callback_data="withdraw_history",
            ),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def show_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    data = get_user(user.id)

    if not data:
        if update.message:
            await update.message.reply_text(
                "❌ Account not found.\n\n"
                "Please use /start first."
            )
        return

    missing = await check_force_join(
        user.id,
        context,
    )

    if missing:
        await show_force_join(
            update,
            context,
            missing,
        )
        return

    balance = float(data.get("balance", 0))
    referrals = int(data.get("referral_count", 0))
    total_earned = float(data.get("total_earned", 0))

    text = (
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "       ✨ *WELCOME TO*\n"
        "     💰 *REFERRAL & EARN*\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"👋 Hey, *{user.first_name}*!\n"
        "🎉 Welcome to our earning community.\n\n"
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        f"💰 *Balance:* ₹{balance:g}\n"
        f"👥 *Referrals:* {referrals}\n"
        f"💎 *Total Earned:* ₹{total_earned:g}\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
        "🎁 Earn *₹5* for every successful referral.\n"
        "💸 Minimum Withdrawal: *₹250*\n\n"
        "👇 *Choose an option below:*"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=main_menu(),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=main_menu(),
            parse_mode="Markdown",
        )
