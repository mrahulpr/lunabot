# plugin/db.py
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URI = os.getenv("MONGO_URI")  # Set in GitHub Actions secrets
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["telegram_bot"]  # Your database name
