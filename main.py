import logging

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
)

from config import BOT_TOKEN
from handlers.start import start_command
from handlers.menu import show_menu
from handlers.callback import button_callback
from handlers.withdraw import withdraw_conversation
from handlers.admin import admin_command
from handlers.admin_callback import admin_callback
from handlers.admin_balance import add_balance_conversation
from handlers.admin_deduct import deduct_balance_conversation
from handlers.broadcast import broadcast_conversation
from handlers.admin_user import (
    find_user_conversation,
    show_user_withdrawal_history,
    toggle_user_block,
)
from handlers.commands import balance_command, referrals_command, referral_command, stats_command, history_command


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is missing in .env")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(
        CommandHandler("start", start_command)
    )

    application.add_handler(
        CommandHandler("menu", show_menu)
    )

    application.add_handler(
        CommandHandler("balance", balance_command)
    )

    application.add_handler(
        CommandHandler("referrals", referrals_command)
    )

    application.add_handler(
        CommandHandler("referral", referral_command)
    )

    application.add_handler(
        CommandHandler("stats", stats_command)
    )

    application.add_handler(
        CommandHandler("history", history_command)
    )

    application.add_handler(
        CommandHandler("admin", admin_command)
    )

    # Admin Add Balance conversation
    application.add_handler(add_balance_conversation)
    application.add_handler(deduct_balance_conversation)
    application.add_handler(broadcast_conversation)

    # Withdrawal conversation
    application.add_handler(withdraw_conversation)

    # Admin Find User conversation
    application.add_handler(find_user_conversation)
    application.add_handler(
        CallbackQueryHandler(
            show_user_withdrawal_history,
            pattern=r"^admin_user_history:[0-9]+$",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            toggle_user_block,
            pattern=r"^admin_(block|unblock)_user:[0-9]+$",
        )
    )
    # Admin callbacks
    application.add_handler(
        CallbackQueryHandler(
            admin_callback,
            pattern=r"^(admin_(withdrawals|history|analytics|refresh|back)|approve:[^ ]+|reject:[^ ]+)$",
        )
    )

    # Other dashboard buttons
    application.add_handler(
        CallbackQueryHandler(
            button_callback,
            pattern="^(balance|referrals|referral_link|stats|check_force_join|withdraw|back_dashboard|withdraw_history)$",
        )
    )

    logger.info("ReferralEarnBot is starting...")

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
