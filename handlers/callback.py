from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes
from urllib.parse import quote

from config import BOT_USERNAME, REFERRAL_REWARD
from database.withdrawals import get_user_withdrawals
from database.users import (
    get_user,
    add_balance,
    increment_referrals,
    is_user_blocked,
)


def back_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔙 Back to Dashboard",
                    callback_data="back_dashboard",
                )
            ]
        ]
    )


async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_data = get_user(user.id)

    if not user_data:
        await query.edit_message_text(
            "❌ Account not found.\n\n"
            "Please use /start first."
        )
        return

    if is_user_blocked(user.id):
        await query.edit_message_text(
            "🚫 *Account Blocked*\n\n"
            "Your account has been blocked by the administrator.\n"
            "You cannot use the bot at this time.",
            parse_mode="Markdown",
        )
        return

    # =========================================================
    # FORCE JOIN CHECK
    # =========================================================
    from handlers.force_join import (
        check_force_join,
        show_force_join,
    )

    # Membership verification
    if query.data == "check_force_join":
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

        pending_referrer = context.user_data.pop(
            "pending_referrer",
            None,
        )

        if pending_referrer:
            add_balance(
                pending_referrer,
                REFERRAL_REWARD,
            )
            increment_referrals(
                pending_referrer,
            )

        await query.edit_message_text(
            "✅ *Membership Verified!*\n\n"
            "🎉 All required channels joined.\n\n"
            "💰 You can now use the bot.",
            parse_mode="Markdown",
        )
        return

    # =========================================================
    # BACK TO DASHBOARD
    # =========================================================
    if query.data == "back_dashboard":
        from handlers.menu import show_menu

        await show_menu(
            update,
            context,
        )
        return

    # Check membership before dashboard actions
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

    # =========================================================
    # WITHDRAWAL HISTORY
    # =========================================================
    if query.data == "withdraw_history":
        withdrawals = list(
            get_user_withdrawals(
                user.id,
                20,
            )
        )

        if not withdrawals:
            await query.edit_message_text(
                "📜 *MY WITHDRAWAL HISTORY*\n\n"
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
            withdrawal_id = str(withdrawal.get("_id", "N/A"))

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
                date_text = created_at.strftime("%d %b %Y • %I:%M %p")
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

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=back_keyboard(),
            parse_mode="Markdown",
        )
        return

        lines = [
            "📜 *My Withdrawal History*",
            "",
        ]

        for withdrawal in withdrawals:
            status = withdrawal.get(
                "status",
                "unknown",
            )

            amount = float(
                withdrawal.get("amount", 0)
            )

            if status == "pending":
                status_text = "⏳ Pending"
            elif status == "approved":
                status_text = "✅ Approved"
            elif status == "rejected":
                status_text = "❌ Rejected"
            else:
                status_text = f"⚠️ {status}"

            lines.append(
                f"{status_text}\n"
                f"💰 Amount: ₹{amount:g}\n"
                f"💳 UPI: `{withdrawal.get('upi_id', '')}`\n"
            )

            lines.append("━━━━━━━━━━━━━━━━")

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=back_keyboard(),
            parse_mode="Markdown",
        )
        return

    # =========================================================
    # DASHBOARD BUTTONS
    # =========================================================

    if query.data == "withdraw":
        return

    elif query.data == "balance":
        await query.edit_message_text(
            "💰 *Your Balance*\n\n"
            f"💵 Available Balance: "
            f"₹{user_data.get('balance', 0):g}\n"
            f"💎 Total Earned: "
            f"₹{user_data.get('total_earned', 0):g}",
            reply_markup=back_keyboard(),
            parse_mode="Markdown",
        )

    elif query.data == "referrals":
        await query.edit_message_text(
            "👥 *My Referrals*\n\n"
            f"Successful Referrals: "
            f"{user_data.get('referral_count', 0)}",
            reply_markup=back_keyboard(),
            parse_mode="Markdown",
        )

    elif query.data == "referral_link":
        referral_link = (
            f"https://t.me/{BOT_USERNAME}?start={user.id}"
        )

        share_text = (
            "🎁 Join this bot and start earning!\n\n"
            "💰 Earn rewards by inviting friends."
        )

        share_url = (
            "https://t.me/share/url?"
            f"url={quote(referral_link)}&"
            f"text={quote(share_text)}"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📤 Share & Earn",
                    url=share_url,
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Back to Dashboard",
                    callback_data="back_dashboard",
                )
            ],
        ])

        await query.edit_message_text(
            "🔗 *Your Referral Link*\n\n"
            f"`{referral_link}`\n\n"
            "📤 Tap the button below to share your link.",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )

    elif query.data == "stats":
        await query.edit_message_text(
            "📊 *Your Statistics*\n\n"
            f"👤 User ID: `{user.id}`\n"
            f"👥 Referrals: "
            f"{user_data.get('referral_count', 0)}\n"
            f"💰 Balance: "
            f"₹{user_data.get('balance', 0):g}\n"
            f"💎 Total Earned: "
            f"₹{user_data.get('total_earned', 0):g}",
            reply_markup=back_keyboard(),
            parse_mode="Markdown",
        )
