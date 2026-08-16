from datetime import datetime, timezone

from database.mongodb import users_collection


def get_user(user_id: int):
    return users_collection.find_one({"user_id": user_id})


def create_user(
    user_id: int,
    username: str = "",
    first_name: str = "",
    referred_by: int | None = None,
):
    existing = get_user(user_id)

    if existing:
        return existing, False

    user = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "balance": 0.0,
        "total_earned": 0.0,
        "referral_count": 0,
        "referred_by": referred_by,
        "created_at": datetime.now(timezone.utc),
    }

    users_collection.insert_one(user)
    return user, True


def add_balance(user_id: int, amount: float):
    users_collection.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "balance": amount,
                "total_earned": amount,
            }
        },
    )


def increment_referrals(user_id: int):
    users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"referral_count": 1}},
    )


def deduct_balance(user_id: int, amount: float):
    result = users_collection.update_one(
        {
            "user_id": user_id,
            "balance": {"$gte": amount},
        },
        {
            "$inc": {
                "balance": -amount,
            }
        },
    )

    return result.modified_count == 1


def get_user_by_id(user_id: int):
    return users_collection.find_one(
        {"user_id": user_id}
    )


def admin_add_balance(user_id: int, amount: float):
    result = users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"balance": amount}},
    )

    return result.modified_count == 1


def admin_deduct_balance(user_id: int, amount: float):
    result = users_collection.update_one(
        {
            "user_id": user_id,
            "balance": {"$gte": amount},
        },
        {
            "$inc": {"balance": -amount},
        },
    )

    return result.modified_count == 1


def get_all_user_ids():
    return users_collection.find(
        {},
        {"user_id": 1, "_id": 0},
    )


def is_user_blocked(user_id: int) -> bool:
    user = get_user(user_id)
    return bool(user and user.get("blocked", False))


def set_user_blocked(user_id: int, blocked: bool) -> bool:
    result = users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"blocked": blocked}},
    )
    return result.modified_count == 1
