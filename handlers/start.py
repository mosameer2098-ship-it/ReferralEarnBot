from telegram import Update
from telegram.ext import ContextTypes

from config import REFERRAL_REWARD
from database.users import (
    create_user,
    add_balance,
    increment_referrals,
    is_user_blocked,
)
from handlers.force_join import (
    check_force_join,
    show_force_join,
)
from handlers.menu import show_menu


async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    if is_user_blocked(user.id):
        await update.message.reply_text(
            "🚫 *Account Blocked*\n\n"
            "Your account has been blocked by the administrator.\n"
            "You cannot use the bot at this time.",
            parse_mode="Markdown",
        )
        return

    referred_by = None

    if context.args:
        try:
            referrer_id = int(context.args[0])

            if referrer_id != user.id:
                referred_by = referrer_id

        except (ValueError, TypeError):
            pass

    user_data, is_new_user = create_user(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        referred_by=referred_by,
    )

    # Save referral until the new user successfully
    # completes the required channel membership.
    if is_new_user and referred_by:
        context.user_data["pending_referrer"] = referred_by

    # Check all required channels.
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

    # Give referral reward only after successful
    # force-join verification.
    pending_referrer = context.user_data.pop(
        "pending_referrer",
        None,
    )

    if is_new_user and pending_referrer:
        add_balance(
            pending_referrer,
            REFERRAL_REWARD,
        )
        increment_referrals(
            pending_referrer,
        )

    # Directly open the final Welcome + Dashboard.
    await show_menu(
        update,
        context,
    )
