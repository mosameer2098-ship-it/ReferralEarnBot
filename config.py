import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "ReferralEarnBot",
)

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "",
).lstrip("@")

# Referral & Withdrawal
REFERRAL_REWARD = 5.0
MIN_WITHDRAW = 250.0

# Force Join Channels
FORCE_CHANNELS = [
    {
        "username": "@Refer2Earn_Officialp",
        "name": "📢 Refer 2 Earn",
    },
    {
        "username": "@DailyBonusOffers",
        "name": "🎁 Daily Bonus Offers",
    },
    {
        "username": "@ReferralEarnUpdates",
        "name": "💰 Referral Earn Updates",
    },
]
