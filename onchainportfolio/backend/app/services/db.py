# app/services/db.py
import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "onchainportfolio")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# collections
users_collection = db["users"]
