import os

from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "inventory_billing_db")
INVENTORY_DB_MODE = os.getenv("INVENTORY_DB_MODE", "auto").strip().lower()
INVENTORY_DEMO_SEED = os.getenv("INVENTORY_DEMO_SEED", "true").strip().lower() in {
	"1",
	"true",
	"yes",
	"on",
}
