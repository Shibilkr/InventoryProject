from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from app.config import INVENTORY_DB_MODE, INVENTORY_DEMO_SEED, MONGODB_DB, MONGODB_URI

try:
    import mongomock
except ImportError:  # pragma: no cover - installed via requirements for runtime use
    mongomock = None


def _build_memory_client():
    if mongomock is None:
        raise RuntimeError(
            "mongomock is required for in-memory demo mode. Install requirements.txt first."
        )
    return mongomock.MongoClient()


def _build_client():
    mode = INVENTORY_DB_MODE
    if mode not in {"auto", "mongodb", "memory"}:
        raise RuntimeError(
            f"Unsupported INVENTORY_DB_MODE='{mode}'. Use auto, mongodb, or memory."
        )

    if mode == "memory":
        return _build_memory_client(), "memory", "In-memory demo data"

    mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    mongo_label = MONGODB_URI if "localhost" in MONGODB_URI else "MongoDB Atlas (cloud)"

    try:
        mongo_client.admin.command("ping")
        return mongo_client, "mongodb", mongo_label
    except ServerSelectionTimeoutError:
        if mode == "mongodb":
            raise
        print("[DB] MongoDB unavailable. Falling back to in-memory demo data.")
        return _build_memory_client(), "memory", "In-memory demo data"


client, DATABASE_BACKEND, DATABASE_LABEL = _build_client()
db = client[MONGODB_DB]


def verify_connection() -> None:
    """Validate the selected database backend and print connection status."""
    if DATABASE_BACKEND == "memory":
        print(f"[DB] ✅  Demo mode active  →  {DATABASE_LABEL}  |  database: {MONGODB_DB}")
        return

    try:
        client.admin.command("ping")
        print(f"[DB] ✅  Connected  →  {DATABASE_LABEL}  |  database: {MONGODB_DB}")
    except ServerSelectionTimeoutError:
        print("[DB] ❌  Could not connect to MongoDB!")
        print("     Check that MongoDB is running OR that your .env MONGODB_URI is correct.")
        raise


def init_indexes() -> None:
    """Create indexes once at startup. Safe to call multiple times (idempotent)."""
    db.products.create_index("barcode", unique=True)
    db.customers.create_index("email", unique=True, sparse=True)
    db.invoices.create_index("customer_id")
    db.invoice_items.create_index("invoice_id")
    db.invoice_items.create_index("product_id")
    print("[DB] ✅  Indexes ready.")


def seed_demo_data() -> None:
    """Seed a presentable demo dataset when running in memory mode."""
    if DATABASE_BACKEND != "memory" or not INVENTORY_DEMO_SEED:
        return
    if any(db[name].count_documents({}) for name in ("suppliers", "products", "customers", "invoices", "invoice_items")):
        return

    now = datetime.now(timezone.utc)

    supplier_one_id = ObjectId()
    supplier_two_id = ObjectId()
    customer_one_id = ObjectId()
    customer_two_id = ObjectId()
    product_one_id = ObjectId()
    product_two_id = ObjectId()
    invoice_id = ObjectId()
    invoice_item_one_id = ObjectId()
    invoice_item_two_id = ObjectId()

    db.suppliers.insert_many([
        {
            "_id": supplier_one_id,
            "name": "Northwind Office Supplies",
            "contact_email": "sales@northwind-demo.com",
            "phone": "+1-555-0100",
            "address": "San Francisco, CA",
            "created_at": now,
            "updated_at": now,
        },
        {
            "_id": supplier_two_id,
            "name": "BluePeak Electronics",
            "contact_email": "hello@bluepeak-demo.com",
            "phone": "+1-555-0142",
            "address": "Seattle, WA",
            "created_at": now,
            "updated_at": now,
        },
    ])

    db.customers.insert_many([
        {
            "_id": customer_one_id,
            "name": "Ava Johnson",
            "email": "ava.johnson@example.com",
            "phone": "+1-555-0201",
            "address": "Austin, TX",
            "created_at": now,
            "updated_at": now,
        },
        {
            "_id": customer_two_id,
            "name": "Liam Chen",
            "email": "liam.chen@example.com",
            "phone": "+1-555-0202",
            "address": "Boston, MA",
            "created_at": now,
            "updated_at": now,
        },
    ])

    db.products.insert_many([
        {
            "_id": product_one_id,
            "name": "Thermal Receipt Printer",
            "barcode": "5901234123457",
            "price": 149.0,
            "stock": 11,
            "supplier_id": supplier_two_id,
            "description": "Compact printer for billing counters",
            "created_at": now,
            "updated_at": now,
        },
        {
            "_id": product_two_id,
            "name": "A4 Paper Pack",
            "barcode": "7351353713572",
            "price": 8.5,
            "stock": 96,
            "supplier_id": supplier_one_id,
            "description": "500-sheet office paper pack",
            "created_at": now,
            "updated_at": now,
        },
    ])

    db.invoices.insert_one(
        {
            "_id": invoice_id,
            "customer_id": customer_one_id,
            "subtotal": 166.0,
            "tax": 8.3,
            "total": 174.3,
            "status": "paid",
            "created_at": now,
            "updated_at": now,
        }
    )

    db.invoice_items.insert_many([
        {
            "_id": invoice_item_one_id,
            "invoice_id": invoice_id,
            "product_id": product_one_id,
            "quantity": 1,
            "unit_price": 149.0,
            "line_total": 149.0,
            "created_at": now,
            "updated_at": now,
        },
        {
            "_id": invoice_item_two_id,
            "invoice_id": invoice_id,
            "product_id": product_two_id,
            "quantity": 2,
            "unit_price": 8.5,
            "line_total": 17.0,
            "created_at": now,
            "updated_at": now,
        },
    ])
    print("[DB] ✅  Demo data seeded.")
