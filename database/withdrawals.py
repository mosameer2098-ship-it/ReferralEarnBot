from datetime import datetime, timezone

from database.mongodb import withdrawals_collection


def create_withdrawal(
    user_id: int,
    amount: float,
    upi_id: str,
):
    withdrawal = {
        "user_id": user_id,
        "amount": amount,
        "upi_id": upi_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
    }

    result = withdrawals_collection.insert_one(withdrawal)

    return str(result.inserted_id)


def get_pending_withdrawals():
    return withdrawals_collection.find(
        {"status": "pending"}
    ).sort("created_at", 1)


def approve_withdrawal(withdrawal_id):
    from bson import ObjectId

    result = withdrawals_collection.update_one(
        {
            "_id": ObjectId(withdrawal_id),
            "status": "pending",
        },
        {
            "$set": {
                "status": "approved",
                "processed_at": datetime.now(timezone.utc),
            }
        },
    )

    return result.modified_count == 1


def reject_withdrawal(withdrawal_id):
    from bson import ObjectId

    result = withdrawals_collection.update_one(
        {
            "_id": ObjectId(withdrawal_id),
            "status": "pending",
        },
        {
            "$set": {
                "status": "rejected",
                "processed_at": datetime.now(timezone.utc),
            }
        },
    )

    return result.modified_count == 1


def get_withdrawal(withdrawal_id):
    from bson import ObjectId

    return withdrawals_collection.find_one(
        {"_id": ObjectId(withdrawal_id)}
    )


def get_all_withdrawals(limit=50):
    return withdrawals_collection.find(
        {}
    ).sort("created_at", -1).limit(limit)

def get_user_withdrawals(user_id: int, limit=20):
    return withdrawals_collection.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(limit)

