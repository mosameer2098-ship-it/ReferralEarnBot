import dns.resolver

from config import MONGO_URI, DATABASE_NAME

# Termux/Android DNS fix
_original_resolver = dns.resolver.Resolver


class TermuxResolver(_original_resolver):
    def __init__(self, *args, **kwargs):
        kwargs["configure"] = False
        super().__init__(*args, **kwargs)
        self.nameservers = ["8.8.8.8", "8.8.4.4"]


dns.resolver.Resolver = TermuxResolver

from pymongo import MongoClient

client = MongoClient(
    MONGO_URI,
    connectTimeoutMS=10000,
    serverSelectionTimeoutMS=10000,
)

db = client[DATABASE_NAME]

users_collection = db["users"]
withdrawals_collection = db["withdrawals"]
