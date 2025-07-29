from motor.motor_asyncio import AsyncIOMotorClient
import os

# Get MongoDB URI from environment variable
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError("❌ MONGO_URI is not set in environment variables!")

# Create the async MongoDB client
client = AsyncIOMotorClient(MONGO_URI)

# You can name the database anything you like here:
db = client["telegram_bot"]
