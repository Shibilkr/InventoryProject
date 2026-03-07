from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from app.config import MONGODB_DB, MONGODB_URI

# Open a connection pool to MongoDB (local or Atlas — set MONGODB_URI in .env)
# MongoClient is lazy: the real TCP connection is made on the first operation.
client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
db = client[MONGODB_DB]


def verify_connection() -> None:
    """Ping MongoDB and print connection status. Called once at startup."""
    try:
        client.admin.command("ping")
        host = MONGODB_URI if "localhost" in MONGODB_URI else "MongoDB Atlas (cloud)"
        print(f"[DB] ✅  Connected  →  {host}  |  database: {MONGODB_DB}")
    except ServerSelectionTimeoutError:
        print("[DB] ❌  Could not connect to MongoDB!")
        print("     Check that MongoDB is running OR that your .env MONGODB_URI is correct.")
        raise


def init_indexes() -> None:
    """Create indexes once at startup. Safe to call multiple times (idempotent)."""
    # Unique barcode per product (EAN-13 auto-generated)
    db.products.create_index("barcode", unique=True)
    # Unique email per customer; sparse = documents without email are excluded
    db.customers.create_index("email", unique=True, sparse=True)
    # Index foreign keys for fast lookups (like SQL FK indexes)
    db.invoices.create_index("customer_id")
    db.invoice_items.create_index("invoice_id")
    db.invoice_items.create_index("product_id")
    print("[DB] ✅  Indexes ready.")
