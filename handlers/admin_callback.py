from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from config import ADMIN_ID
from database.withdrawals import (
    get_pending_withdrawals,
    get_all_withdrawals,
    get_withdrawal,
    approve_withdrawal,
    reject_withdrawal,
)
from database.users import add_balance


def admin_back_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔙 Back to Admin Panel",
                    callback_data="admin_back",
                )
            ]
        ]
    )


async def admin_callback(
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

    data = query.data

    # =========================================================
    # BACK TO ADMIN PANEL
    # =========================================================
    if data == "admin_back":
        from handlers.admin import (
            get_admin_text,
            admin_keyboard,
        )

        await query.edit_message_text(
            get_admin_text(),
            reply_markup=admin_keyboard(),
            parse_mode="Markdown",
        )
        return

    # =========================================================
    # ANALYTICS
    # =========================================================
    if data == "admin_analytics":
        from handlers.admin import get_analytics_text

        await query.edit_message_text(
            get_analytics_text(),
            reply_markup=admin_back_keyboard(),
            parse_mode="Markdown",
        )
        return

    # =========================================================
    # PENDING WITHDRAWALS
    # =========================================================
    if data == "admin_withdrawals":
        withdrawals = list(
            get_pending_withdrawals()
        )

        if not withdrawals:
            await query.edit_message_text(
                "📋 *Pending Withdrawals*\n\n"
                "✅ No pending withdrawal requests.",
                reply_markup=admin_back_keyboard(),
                parse_mode="Markdown",
            )
            return

        await query.edit_message_text(
            "📋 *Pending Withdrawals*\n\n"
            f"Found {len(withdrawals)} "
            "pending request(s).\n\n"
            "👇 Requests are shown below.",
            reply_markup=admin_back_keyboard(),
            parse_mode="Markdown",
        )

        for withdrawal in withdrawals:
            withdrawal_id = str(
                withdrawal["_id"]
            )
            user_id = withdrawal["user_id"]
            amount = float(
                withdrawal["amount"]
            )
            upi_id = withdrawal["upi_id"]

            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ Approve",
                        callback_data=(
                            f"approve:{withdrawal_id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        "❌ Reject",
                        callback_data=(
                            f"reject:{withdrawal_id}"
                        ),
                    ),
                ]
            ]

            await query.message.reply_text(
                "💸 *Withdrawal Request*\n\n"
                f"👤 User ID: `{user_id}`\n"
                f"💰 Amount: ₹{amount:g}\n"
                f"💳 UPI ID: `{upi_id}`\n"
                f"🆔 Request ID: `{withdrawal_id}`\n\n"
                "⏳ Status: Pending",
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                ),
                parse_mode="Markdown",
            )

        return

    # =========================================================
    # WITHDRAWAL HISTORY
    # =========================================================
    if data == "admin_history":
        withdrawals = list(
            get_all_withdrawals(50)
        )

        if not withdrawals:
            await query.edit_message_text(
                "📜 *WITHDRAWAL HISTORY*\n\n"
                "📭 No withdrawal requests found.",
                reply_markup=admin_back_keyboard(),
                parse_mode="Markdown",
            )
            return

        lines = [
            "📜 *WITHDRAWAL HISTORY*",
            "",
        ]

        for index, withdrawal in enumerate(withdrawals, 1):
            status = withdrawal.get("status", "unknown")
            amount = float(withdrawal.get("amount", 0))
            user_id = withdrawal.get("user_id", "N/A")
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
            processed_at = withdrawal.get("processed_at")

            if created_at:
                created_text = created_at.strftime(
                    "%d %b %Y • %I:%M %p"
                )
            else:
                created_text = "N/A"

            if processed_at:
                processed_text = processed_at.strftime(
                    "%d %b %Y • %I:%M %p"
                )
            else:
                processed_text = "Not processed"

            lines.append(
                f"🔹 *Request #{index}*\n"
                f"🆔 ID: `{withdrawal_id}`\n"
                f"👤 User ID: `{user_id}`\n"
                f"💰 Amount: ₹{amount:g}\n"
                f"💳 UPI: `{upi_id}`\n"
                f"📌 Status: {status_text}\n"
                f"📅 Requested: {created_text}\n"
                f"⏱️ Processed: {processed_text}\n"
                "━━━━━━━━━━━━━━━━━━━━"
            )

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=admin_back_keyboard(),
            parse_mode="Markdown",
        )
        return

        lines = [
            "📜 *Withdrawal History*",
            "",
        ]

        for withdrawal in withdrawals:
            status = withdrawal.get(
                "status",
                "unknown",
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
                f"{status_text} | "
                f"₹{float(withdrawal['amount']):g} | "
                f"`{withdrawal['user_id']}`"
            )

        await query.edit_message_text(
            "\n".join(lines),
            reply_markup=admin_back_keyboard(),
            parse_mode="Markdown",
        )
        return

    # =========================================================
    # REFRESH
    # =========================================================
    if data == "admin_refresh":
        from handlers.admin import (
            get_admin_text,
            admin_keyboard,
        )

        await query.edit_message_text(
            get_admin_text(),
            reply_markup=admin_keyboard(),
            parse_mode="Markdown",
        )
        return

    # =========================================================
    # APPROVE / REJECT
    # =========================================================
    if ":" not in data:
        return

    action, withdrawal_id = data.split(
        ":",
        1,
    )

    if action not in (
        "approve",
        "reject",
    ):
        return

    withdrawal = get_withdrawal(
        withdrawal_id
    )

    if not withdrawal:
        await query.edit_message_text(
            "❌ Withdrawal request not found."
        )
        return

    if withdrawal.get("status") != "pending":
        await query.edit_message_text(
            "⚠️ This request is already "
            f"*{withdrawal.get('status', 'processed')}*.",
            parse_mode="Markdown",
        )
        return

    user_id = withdrawal["user_id"]
    amount = float(withdrawal["amount"])

    # =========================================================
    # APPROVE
    # =========================================================
    if action == "approve":
        success = approve_withdrawal(
            withdrawal_id
        )

        if not success:
            await query.edit_message_text(
                "⚠️ This withdrawal was already processed."
            )
            return

        await query.edit_message_text(
            "✅ *Withdrawal Approved*\n\n"
            f"💰 Amount: ₹{amount:g}\n"
            f"👤 User ID: `{user_id}`\n"
            f"🆔 Request ID: `{withdrawal_id}`",
            reply_markup=admin_back_keyboard(),
            parse_mode="Markdown",
        )

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "✅ *Withdrawal Approved!*\n\n"
                    f"💰 Amount: ₹{amount:g}\n"
                    f"💳 UPI ID: "
                    f"`{withdrawal['upi_id']}`\n\n"
                    "Your withdrawal has been approved."
                ),
                parse_mode="Markdown",
            )
        except Exception:
            pass

        return

    # =========================================================
    # REJECT
    # =========================================================
    if action == "reject":
        success = reject_withdrawal(
            withdrawal_id
        )

        if not success:
            await query.edit_message_text(
                "⚠️ This withdrawal was already processed."
            )
            return

        # Refund rejected amount.
        add_balance(
            user_id,
            amount,
        )

        await query.edit_message_text(
            "❌ *Withdrawal Rejected*\n\n"
            f"💰 Refunded: ₹{amount:g}\n"
            f"👤 User ID: `{user_id}`\n"
            f"🆔 Request ID: `{withdrawal_id}`",
            reply_markup=admin_back_keyboard(),
            parse_mode="Markdown",
        )

        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "❌ *Withdrawal Rejected*\n\n"
                    f"💰 Amount Refunded: "
                    f"₹{amount:g}\n\n"
                    "The amount has been returned "
                    "to your bot balance."
                ),
                parse_mode="Markdown",
            )
        except Exception:
            pass

        return
