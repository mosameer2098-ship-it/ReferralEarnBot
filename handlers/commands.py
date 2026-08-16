from telegram import Update
from telegram.ext import ContextTypes

from database.users import get_user
from database.withdrawals import get_user_withdrawals
from handlers.callback import back_keyboard


async def balance_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    user_data = get_user(user.id)

    if not user_data:
        await update.message.reply_text(
            "❌ Account not found.\n\n"
            "Please use /start first."
        )
        return

    await update.message.reply_text(
        "💰 *Your Balance*\n\n"
        f"💵 Available Balance: ₹{user_data.get('balance', 0):g}\n"
        f"💎 Total Earned: ₹{user_data.get('total_earned', 0):g}",
        reply_markup=back_keyboard(),
        parse_mode="Markdown",
    )


async def referrals_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    user_data = get_user(user.id)

    if not user_data:
        await update.message.reply_text(
            "❌ Account not found.\n\n"
            "Please use /start first."
        )
        return

    await update.message.reply_text(
        "👥 *My Referrals*\n\n"
        f"Successful Referrals: "
        f"{user_data.get('referral_count', 0)}",
        reply_markup=back_keyboard(),
        parse_mode="Markdown",
    )


async def referral_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    user_data = get_user(user.id)

    if not user_data:
        await update.message.reply_text(
            "❌ Account not found.\n\n"
            "Please use /start first."
        )
        return

    from config import BOT_USERNAME

    referral_link = (
        f"https://t.me/{BOT_USERNAME}?start={user.id}"
    )

    await update.message.reply_text(
        "🔗 *Your Referral Link*\n\n"
        f"`{referral_link}`\n\n"
        "👥 Share this link with your friends.\n"
        "🎁 Earn rewards for every successful referral.",
        reply_markup=back_keyboard(),
        parse_mode="Markdown",
    )


async def stats_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    user_data = get_user(user.id)

    if not user_data:
        await update.message.reply_text(
            "❌ Account not found.\n\n"
            "Please use /start first."
        )
        return

    await update.message.reply_text(
        "📊 *Your Statistics*\n\n"
        f"👤 User ID: `{user.id}`\n"
        f"👥 Referrals: {user_data.get('referral_count', 0)}\n"
        f"💰 Balance: ₹{user_data.get('balance', 0):g}\n"
        f"💎 Total Earned: ₹{user_data.get('total_earned', 0):g}",
        reply_markup=back_keyboard(),
        parse_mode="Markdown",
    )


async def history_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    user_data = get_user(user.id)

    if not user_data:
        await update.message.reply_text(
            "❌ Account not found.\n\n"
            "Please use /start first."
        )
        return

    withdrawals = list(
        get_user_withdrawals(user.id, 20)
    )

    if not withdrawals:
        await update.message.reply_text(
            "📜 *My Withdrawal History*\n\n"
            "📭 No withdrawal requests found yet.",
            reply_markup=back_keyboard(),
            parse_mode="Markdown",
        )
        return

    lines = [
        "📜 *MY WITHDRAWAL HISTORY*",
        "",
    ]

    for index, withdrawal in enumerate(withdrawals, 1):
        status = withdrawal.get("status", "unknown")
        amount = float(withdrawal.get("amount", 0))
        upi_id = withdrawal.get("upi_id", "N/A")
        withdrawal_id = str(
            withdrawal.get("_id", "N/A")
        )

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
            date_text = created_at.strftime(
                "%d %b %Y • %I:%M %p"
            )
        else:
            date_text = "N/A"

        lines.append(
            f"🔹 *Request #{index}*\n"
            f"🆔 ID: `{withdrawal_id}`\n"
            f"💰 Amount: ₹{amount:g}\n"
            f"💳 UPI: `{upi_id}`\n"
            f"📌 Status: {status_text}\n"
            f"📅 Date: {date_text}\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )

    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=back_keyboard(),
        parse_mode="Markdown",
    )
